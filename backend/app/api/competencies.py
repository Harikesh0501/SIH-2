from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.competency import Competency, CompetencyLevel, RoleBenchmark, UserCompetency
from app.schemas.competency import (
    CompetencyResponse,
    CompetencyLevelResponse,
    GapAnalysisResponse,
    CareerSimulationRequest,
    CareerSimulationResponse,
    SupervisorCalibrateRequest,
    SupervisorCalibrateResponse,
    TeamMatrixResponse,
    SubordinateMatrixItem,
    SubordinateCompetencyScore,
    TeamGapAggregate,
)
from app.services.gap_analyzer import CompetencyGapAnalyzer
from app.api.deps import get_current_user, require_supervisor
from app.data.framework_loader import load_competency_framework

router = APIRouter(prefix="/competencies", tags=["Competency Framework & Gap Analysis"])

@router.get("/framework", response_model=Dict[str, Any])
def get_framework():
    """
    Returns the complete MoSPI Official Statistical Competency Framework dictionary.
    """
    return load_competency_framework()

@router.get("/user-status")
def get_user_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated officer's evaluated competency levels versus role benchmarks.
    """
    benchmarks = db.query(RoleBenchmark).filter(RoleBenchmark.designation == current_user.designation).all()
    user_comps = {
        uc.competency_id: uc
        for uc in db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    }

    result = []
    for bm in benchmarks:
        comp = bm.competency
        if not comp:
            continue
        uc = user_comps.get(comp.id)
        current_lvl = uc.current_level if uc else 1
        assessed_via = uc.assessed_via if uc else "NOT_ASSESSED"
        conf = uc.confidence_score if uc else 0.0

        result.append({
            "competency_id": comp.id,
            "code": comp.code,
            "name": comp.name,
            "domain": comp.domain,
            "current_level": current_lvl,
            "required_level": bm.required_level,
            "is_mandatory": bm.is_mandatory,
            "assessed_via": assessed_via,
            "confidence_score": conf,
            "is_met": current_lvl >= bm.required_level,
        })

    return {
        "officer_name": current_user.full_name,
        "designation": current_user.designation,
        "cadre": current_user.cadre,
        "competencies": result,
    }

@router.get("/gap-analysis", response_model=GapAnalysisResponse)
def get_gap_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Performs real-time competency gap diagnosis and delivers radar-chart formatted data.
    """
    return CompetencyGapAnalyzer.analyze_gaps(db, current_user)

@router.post("/career-simulation", response_model=CareerSimulationResponse)
def simulate_career_pathway(
    req: CareerSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Projects future competency requirements and upskilling roadmap for a target designation.
    """
    return CompetencyGapAnalyzer.simulate_career_pathway(db, current_user, req.target_designation)

@router.get("/team-matrix", response_model=TeamMatrixResponse)
def get_team_matrix(
    division: Optional[str] = Query(None, description="Optional division filter for leadership"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """
    Returns aggregated team competency matrix and readiness analytics for supervisors and division heads.
    """
    if current_user.role == "ADMIN":
        query = db.query(User).filter(User.id != current_user.id)
        if division:
            query = query.filter(User.division == division)
        subs = query.all()
    else:
        # Supervisor or Trainer: direct reports OR officers in their division
        subs = db.query(User).filter(
            (User.supervisor_id == current_user.id) | (User.division == current_user.division),
            User.id != current_user.id
        ).all()

    # Fetch all active competencies for columns
    all_comps = db.query(Competency).order_by(Competency.domain, Competency.code).all()
    competency_columns = [
        {"code": c.code, "name": c.name, "domain": c.domain}
        for c in all_comps
    ]

    subordinate_items: List[SubordinateMatrixItem] = []
    total_readiness_sum = 0.0
    distribution = {"ready": 0, "developing": 0, "needs_attention": 0}
    team_gaps_map: Dict[str, Dict[str, Any]] = {}

    for s in subs:
        gap_res = CompetencyGapAnalyzer.analyze_gaps(db, s)
        readiness = gap_res.overall_readiness_percentage
        total_readiness_sum += readiness

        if readiness >= 80.0:
            distribution["ready"] += 1
        elif readiness >= 50.0:
            distribution["developing"] += 1
        else:
            distribution["needs_attention"] += 1

        crit_count = 0
        mod_count = 0
        comp_scores: List[SubordinateCompetencyScore] = []

        for item in gap_res.all_competencies:
            if item.gap >= 2 or item.urgency_score >= 2.0:
                crit_count += 1
            elif item.gap == 1:
                mod_count += 1

            comp_scores.append(SubordinateCompetencyScore(
                competency_id=item.competency_id,
                code=item.code,
                name=item.name,
                domain=item.domain,
                current_level=item.current_level,
                required_level=item.required_level,
                gap=item.gap,
                status=item.status,
                assessed_via=item.assessed_via,
            ))

            # Track aggregate team gap
            if item.gap > 0:
                if item.code not in team_gaps_map:
                    team_gaps_map[item.code] = {
                        "code": item.code,
                        "name": item.name,
                        "domain": item.domain,
                        "count": 0,
                        "total_gap": 0,
                        "total_urgency": 0.0,
                    }
                team_gaps_map[item.code]["count"] += 1
                team_gaps_map[item.code]["total_gap"] += item.gap
                team_gaps_map[item.code]["total_urgency"] += item.urgency_score

        subordinate_items.append(SubordinateMatrixItem(
            id=s.id,
            full_name=s.full_name,
            email=s.email,
            designation=s.designation,
            division=s.division,
            cadre=s.cadre,
            experience_years=s.experience_years or 0,
            readiness_percentage=readiness,
            critical_gaps_count=crit_count,
            moderate_gaps_count=mod_count,
            competencies=comp_scores,
        ))

    total_count = len(subs)
    avg_readiness = round(total_readiness_sum / total_count, 1) if total_count > 0 else 100.0

    # Build top team gaps
    top_gaps: List[TeamGapAggregate] = []
    for code, g_data in team_gaps_map.items():
        cnt = g_data["count"]
        top_gaps.append(TeamGapAggregate(
            competency_code=g_data["code"],
            competency_name=g_data["name"],
            domain=g_data["domain"],
            affected_officers_count=cnt,
            average_gap=round(g_data["total_gap"] / cnt, 1),
            total_urgency_score=round(g_data["total_urgency"], 2),
        ))
    top_gaps.sort(key=lambda x: x.total_urgency_score, reverse=True)

    return TeamMatrixResponse(
        supervisor_id=current_user.id,
        supervisor_name=current_user.full_name,
        division=division or current_user.division,
        total_subordinates=total_count,
        average_team_readiness=avg_readiness,
        distribution=distribution,
        top_team_gaps=top_gaps[:5],
        competency_columns=competency_columns,
        subordinates=subordinate_items,
    )

@router.post("/supervisor-calibrate", response_model=SupervisorCalibrateResponse)
def supervisor_calibrate(
    req: SupervisorCalibrateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """
    Allows supervisors and cadre administrators to calibrate subordinate competency ratings.
    """
    if req.calibrated_level < 1 or req.calibrated_level > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calibrated level must be an integer between 1 and 5.",
        )

    subordinate = db.query(User).filter(User.id == req.subordinate_id).first()
    if not subordinate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subordinate officer with ID {req.subordinate_id} not found.",
        )

    # Check supervisory relationship
    if current_user.role != "ADMIN":
        if subordinate.supervisor_id != current_user.id and subordinate.division != current_user.division:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are only authorized to calibrate ratings for officers reporting directly to you or in your division.",
            )

    competency = db.query(Competency).filter(Competency.id == req.competency_id).first()
    if not competency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competency with ID {req.competency_id} not found.",
        )

    # Upsert UserCompetency
    uc = db.query(UserCompetency).filter(
        UserCompetency.user_id == subordinate.id,
        UserCompetency.competency_id == competency.id,
    ).first()

    if uc:
        uc.current_level = req.calibrated_level
        uc.assessed_via = "SUPERVISOR"
        uc.confidence_score = 0.95
        uc.last_evaluated_at = datetime.utcnow()
    else:
        uc = UserCompetency(
            user_id=subordinate.id,
            competency_id=competency.id,
            current_level=req.calibrated_level,
            assessed_via="SUPERVISOR",
            confidence_score=0.95,
            last_evaluated_at=datetime.utcnow(),
        )
        db.add(uc)

    db.commit()
    db.refresh(uc)

    # Recalculate gap analysis for subordinate to get updated readiness
    updated_analysis = CompetencyGapAnalyzer.analyze_gaps(db, subordinate)

    return SupervisorCalibrateResponse(
        success=True,
        message=f"Successfully calibrated competency {competency.code} ({competency.name}) for {subordinate.full_name} to Level {req.calibrated_level}.",
        subordinate_id=subordinate.id,
        subordinate_name=subordinate.full_name,
        competency_code=competency.code,
        competency_name=competency.name,
        new_level=req.calibrated_level,
        assessed_via="SUPERVISOR",
        new_readiness_percentage=updated_analysis.overall_readiness_percentage,
    )

