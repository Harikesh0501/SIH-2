from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.user import User
from app.models.competency import Competency, RoleBenchmark, UserCompetency, CompetencyDomain
from app.schemas.competency import (
    CompetencyGapItem,
    DomainGapSummary,
    GapAnalysisResponse,
    CareerSimulationResponse,
)

class CompetencyGapAnalyzer:
    @staticmethod
    def analyze_gaps(db: Session, user: User, override_designation: Optional[str] = None) -> GapAnalysisResponse:
        active_designation = override_designation or user.designation

        # Fetch benchmarks for this designation with eager loading of competency
        benchmarks = db.query(RoleBenchmark).options(joinedload(RoleBenchmark.competency)).filter(RoleBenchmark.designation == active_designation).all()
        if not benchmarks:
            # Fallback to Junior Statistical Officer benchmarks if custom designation not found
            benchmarks = db.query(RoleBenchmark).options(joinedload(RoleBenchmark.competency)).filter(RoleBenchmark.designation == "Junior Statistical Officer").all()

        # Map of user's current competencies
        user_comps = {
            uc.competency_id: uc
            for uc in db.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()
        }

        all_items: List[CompetencyGapItem] = []
        domain_buckets: Dict[str, Dict[str, Any]] = {
            CompetencyDomain.STATISTICAL.value: {"current": 0, "required": 0, "gap": 0, "count": 0},
            CompetencyDomain.TECHNICAL.value: {"current": 0, "required": 0, "gap": 0, "count": 0},
            CompetencyDomain.DIGITAL_GOVERNANCE.value: {"current": 0, "required": 0, "gap": 0, "count": 0},
            CompetencyDomain.BEHAVIOURAL_MANAGERIAL.value: {"current": 0, "required": 0, "gap": 0, "count": 0},
        }

        total_required_sum = 0
        total_acquired_sum = 0
        radar_data: List[Dict[str, Any]] = []

        for b in benchmarks:
            comp: Competency = b.competency
            if not comp:
                continue

            user_comp = user_comps.get(comp.id)
            current_level = user_comp.current_level if user_comp else 1
            assessed_via = user_comp.assessed_via if user_comp else "SELF_BASELINE"

            gap = max(0, b.required_level - current_level)
            urgency_score = round(gap * b.weight * (1.5 if b.is_mandatory else 1.0), 2)

            if gap >= 2:
                status = "CRITICAL_GAP"
            elif gap == 1:
                status = "MODERATE_GAP"
            elif current_level > b.required_level:
                status = "EXCEEDS"
            else:
                status = "ON_TRACK"

            item = CompetencyGapItem(
                competency_id=comp.id,
                code=comp.code,
                name=comp.name,
                domain=comp.domain,
                current_level=current_level,
                required_level=b.required_level,
                gap=gap,
                is_mandatory=b.is_mandatory,
                weight=b.weight,
                urgency_score=urgency_score,
                status=status,
                assessed_via=assessed_via,
            )
            all_items.append(item)

            # Update domain aggregates
            domain_key = comp.domain
            if domain_key in domain_buckets:
                domain_buckets[domain_key]["current"] += current_level
                domain_buckets[domain_key]["required"] += b.required_level
                domain_buckets[domain_key]["gap"] += gap
                domain_buckets[domain_key]["count"] += 1

            total_required_sum += b.required_level
            total_acquired_sum += min(current_level, b.required_level)

            # Add to radar data
            radar_data.append({
                "subject": comp.code,
                "name": comp.name,
                "current": current_level,
                "required": b.required_level,
                "fullMark": 5,
                "domain": comp.domain,
            })

        # Calculate overall readiness percentage
        overall_readiness = (
            round((total_acquired_sum / total_required_sum) * 100, 1)
            if total_required_sum > 0
            else 100.0
        )

        # Build domain summaries
        domain_summaries: List[DomainGapSummary] = []
        for d_name, d_data in domain_buckets.items():
            count = d_data["count"]
            if count > 0:
                avg_curr = round(d_data["current"] / count, 1)
                avg_req = round(d_data["required"] / count, 1)
                readiness = round((d_data["current"] / max(1, d_data["required"])) * 100, 1)
                readiness = min(100.0, readiness)
            else:
                avg_curr = 0.0
                avg_req = 0.0
                readiness = 100.0

            domain_summaries.append(
                DomainGapSummary(
                    domain=d_name,
                    average_current_level=avg_curr,
                    average_required_level=avg_req,
                    total_gap=d_data["gap"],
                    readiness_percentage=readiness,
                )
            )

        # Sort high urgency gaps descending by score
        high_urgency_gaps = sorted(
            [item for item in all_items if item.gap > 0],
            key=lambda x: x.urgency_score,
            reverse=True,
        )

        return GapAnalysisResponse(
            officer_name=user.full_name,
            designation=active_designation,
            cadre=user.cadre,
            division=user.division,
            overall_readiness_percentage=overall_readiness,
            domain_summaries=domain_summaries,
            radar_data=radar_data[:8], # clean top 8 for radar visual
            high_urgency_gaps=high_urgency_gaps,
            all_competencies=all_items,
        )

    @staticmethod
    def simulate_career_pathway(
        db: Session, user: User, target_designation: str
    ) -> CareerSimulationResponse:
        analysis = CompetencyGapAnalyzer.analyze_gaps(
            db, user, override_designation=target_designation
        )

        recommendations = []
        for gap in analysis.high_urgency_gaps[:5]:
            recommendations.append(
                f"Upskill in {gap.name} ({gap.code}): Advance from Level {gap.current_level} to Level {gap.required_level}."
            )

        if not recommendations:
            recommendations.append(
                f"You currently fulfill all standard competency benchmarks for {target_designation}!"
            )

        return CareerSimulationResponse(
            current_designation=user.designation,
            target_designation=target_designation,
            readiness_percentage=analysis.overall_readiness_percentage,
            projected_gaps=analysis.high_urgency_gaps,
            recommended_pathway_summary=recommendations,
        )
