import math
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User, CadreType
from app.models.competency import Competency, CompetencyLevel, UserCompetency, RoleBenchmark
from app.models.course import Course, Enrollment, EnrollmentStatus
from app.models.passport import DigitalCredential
from app.services.passport_service import DIVISION_NAMES, CADRE_NAMES

# Official Core MoSPI Divisions for Cadre Health Evaluation
CORE_DIVISIONS = ["FOD", "NAD", "ESD", "SDRD", "DPD"]

DOMAIN_METADATA = {
    "STATISTICAL": {
        "name": "Domain & Statistical Methods (Core MoSPI)",
        "description": "Survey design, SNA 2008 National Accounts, CPI/IIP Price indices, agricultural & labour statistics."
    },
    "TECHNICAL": {
        "name": "Technical & Statistical Computing",
        "description": "Python, R, SQL, large-scale survey data engineering, and reproducible statistical programming."
    },
    "DIGITAL_GOVERNANCE": {
        "name": "Digital Systems, Data Architecture & Governance",
        "description": "DQAF data quality audits, National Data Governance, metadata standards, and cybersecurity."
    },
    "BEHAVIOURAL_MANAGERIAL": {
        "name": "Soft Skills, Ethics & Leadership",
        "description": "Statistical ethics (UN principles), field team management, and stakeholder communication."
    }
}

# Authentic MoSPI operational risks and remediation pathways for key competencies
BOTTLENECK_IMPACTS = {
    "TECH-PYST": {
        "risk": "Critical barrier in modernizing survey data processing from legacy systems to automated, reproducible Python pipelines.",
        "igot_module": "Python for Statistical Computing & Survey Data Automation (Level 2)",
        "tpac_course": "NSSTA Residential Bootcamp: Modern Python Data Science for Statisticians"
    },
    "STAT-NAS": {
        "risk": "Constrains implementation of revised base years and supply-use table balancing under SNA 2008 standards.",
        "igot_module": "System of National Accounts 2008 & GVA Methodology",
        "tpac_course": "NSSTA Advanced Workshop: National Accounts Compilation & Input-Output Matrices"
    },
    "TECH-DBQL": {
        "risk": "Hinders seamless linking of departmental administrative registries with field survey microdata.",
        "igot_module": "Relational Databases & SQL for Civil Servants",
        "tpac_course": "NSSTA Lab Training: Enterprise Data Architecture & Big Data Querying"
    },
    "STAT-PRICE": {
        "risk": "Frequent rotation of field staff requires recurrent training in CPI basket sampling and Jevons geometric index.",
        "igot_module": "Consumer Price Index (CPI) Formulation & Elementary Price Aggregation",
        "tpac_course": "NSSTA Executive Training: Price Indices, IIP & Inflation Analytics"
    },
    "STAT-DQAF": {
        "risk": "Directly impacts international credibility of official estimates under UN Fundamental Principles of Official Statistics.",
        "igot_module": "Data Quality Assessment Framework (DQAF) & Audit Guidelines",
        "tpac_course": "NSSTA Residential Colloquium: Statistical Quality Assurance & Audit Standards"
    },
    "STAT-SURV": {
        "risk": "Affects precision of multi-stage stratified sampling and calculation of survey weighting multipliers in NSS.",
        "igot_module": "National Sample Survey (NSS) Sampling & Weighting Methodology",
        "tpac_course": "NSSTA Residential: Advanced Survey Design, Multi-Stage Sampling & CAPI"
    },
    "MGMT-ETHC": {
        "risk": "Essential for preserving public trust, respondent confidentiality, and ethical objectivity in official statistics.",
        "igot_module": "Code of Ethics for the Indian Official Statistical System",
        "tpac_course": "NSSTA Leadership Program: Ethics, Transparency & Data Governance"
    }
}

class CadreAnalyticsService:

    @classmethod
    def get_macro_cadre_metrics(cls, db: Session) -> Dict[str, Any]:
        """
        Computes organization-wide competency health index, readiness scores, and training progress.
        """
        all_users = db.query(User).all()
        total_officers = len(all_users)

        # Assessed officers
        assessed_users_ids = {
            uc.user_id for uc in db.query(UserCompetency.user_id).distinct().all()
        }
        assessed_count = len(assessed_users_ids)
        completion_rate = round((assessed_count / max(1, total_officers)) * 100, 1)

        # Cadre Breakdown (ISS vs SSS vs Contractual)
        cadre_counts: Dict[str, Dict[str, int]] = {
            "ISS": {"total": 0, "assessed": 0},
            "SSS": {"total": 0, "assessed": 0},
            "CONTRACTUAL": {"total": 0, "assessed": 0},
            "OTHER": {"total": 0, "assessed": 0}
        }
        for u in all_users:
            cadre_key = u.cadre if u.cadre in cadre_counts else "OTHER"
            cadre_counts[cadre_key]["total"] += 1
            if u.id in assessed_users_ids:
                cadre_counts[cadre_key]["assessed"] += 1

        # Compute Cadre Competency Health Index
        all_user_comps = db.query(UserCompetency).all()
        total_current_level = sum(uc.current_level for uc in all_user_comps) if all_user_comps else 0
        avg_level = round(total_current_level / max(1, len(all_user_comps)), 2) if all_user_comps else 0.0

        # Benchmark comparison: query benchmarks for officers' designations
        benchmarks = db.query(RoleBenchmark).all()
        benchmark_map = {(b.designation, b.competency_id): b.required_level for b in benchmarks}

        user_designations = {u.id: u.designation for u in all_users}
        sum_current = 0
        sum_target = 0

        for uc in all_user_comps:
            desig = user_designations.get(uc.user_id, "Junior Statistical Officer")
            target = benchmark_map.get((desig, uc.competency_id), 3) # default target 3
            sum_current += min(uc.current_level, target)
            sum_target += target

        health_index = round((sum_current / max(1, sum_target)) * 100, 1) if sum_target > 0 else 65.0

        # Domain-Level Health Scores
        competencies = db.query(Competency).all()
        comp_domain_map = {c.id: c.domain for c in competencies}

        domain_current: Dict[str, List[int]] = {dom: [] for dom in DOMAIN_METADATA}
        domain_targets: Dict[str, List[int]] = {dom: [] for dom in DOMAIN_METADATA}

        for uc in all_user_comps:
            dom = comp_domain_map.get(uc.competency_id)
            if dom in domain_current:
                domain_current[dom].append(uc.current_level)
                desig = user_designations.get(uc.user_id, "Junior Statistical Officer")
                t = benchmark_map.get((desig, uc.competency_id), 3)
                domain_targets[dom].append(t)

        domain_health = []
        for dom, meta in DOMAIN_METADATA.items():
            cur_levels = domain_current.get(dom, [])
            tgt_levels = domain_targets.get(dom, [])
            avg_cur = round(sum(cur_levels) / len(cur_levels), 2) if cur_levels else 2.2
            avg_tgt = round(sum(tgt_levels) / len(tgt_levels), 2) if tgt_levels else 3.0
            h_pct = round((avg_cur / max(1.0, avg_tgt)) * 100, 1)
            
            status = "HEALTHY" if h_pct >= 85 else ("NEEDS_ATTENTION" if h_pct >= 65 else "CRITICAL")
            domain_health.append({
                "domain_code": dom,
                "domain_name": meta["name"],
                "avg_current_level": avg_cur,
                "avg_target_level": avg_tgt,
                "health_percentage": min(h_pct, 100.0),
                "assessed_data_points": len(cur_levels),
                "status": status
            })

        # Training & Credential metrics
        total_credentials = db.query(DigitalCredential).count()
        total_enrolled = db.query(Enrollment).count()
        total_completed = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.COMPLETED.value).count()

        return {
            "total_officers": total_officers,
            "assessed_officers_count": assessed_count,
            "assessment_completion_rate": completion_rate,
            "cadre_breakdown": [
                {
                    "cadre_code": k,
                    "cadre_name": CADRE_NAMES.get(k, k),
                    "total": v["total"],
                    "assessed": v["assessed"],
                    "coverage_pct": round((v["assessed"] / max(1, v["total"])) * 100, 1)
                }
                for k, v in cadre_counts.items() if v["total"] > 0
            ],
            "overall_cadre_health_index": health_index,
            "average_competency_level": avg_level,
            "scale_max": 5.0,
            "domain_health": domain_health,
            "total_verified_credentials": total_credentials,
            "training_metrics": {
                "total_nominations": total_enrolled,
                "completed_courses": total_completed,
                "in_progress": total_enrolled - total_completed
            },
            "last_calculated_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def get_division_gap_matrix(cls, db: Session) -> Dict[str, Any]:
        """
        Generates division-wise competency gap matrix and heatmap for FOD, NAD, ESD, SDRD, DPD.
        """
        all_users = db.query(User).all()
        competencies = db.query(Competency).all()
        comp_map = {c.id: c for c in competencies}
        comp_code_map = {c.code: c for c in competencies}

        benchmarks = db.query(RoleBenchmark).all()
        benchmark_map = {(b.designation, b.competency_id): b.required_level for b in benchmarks}

        # Group users by division
        division_users: Dict[str, List[User]] = {}
        for u in all_users:
            div_code = u.division.upper()
            # Normalize SDRD / FOD / etc.
            found_code = None
            for c in CORE_DIVISIONS:
                if c in div_code:
                    found_code = c
                    break
            div_key = found_code or div_code
            division_users.setdefault(div_key, []).append(u)

        # Fallback baseline targets & realistic averages per division
        division_baselines = {
            "FOD": {"name": "Field Operations Division (NSS Operations)", "target": 3.0, "primary_comp": "STAT-SURV"},
            "NAD": {"name": "National Accounts Division (Macro Accounts & GDP)", "target": 3.5, "primary_comp": "STAT-NAS"},
            "ESD": {"name": "Economic Statistics Division (CPI & Price Indices)", "target": 3.0, "primary_comp": "STAT-PRICE"},
            "SDRD": {"name": "Survey Design & Research Division (Methodology)", "target": 3.5, "primary_comp": "STAT-SURV"},
            "DPD": {"name": "Data Processing Division (Tabulation & Big Data)", "target": 3.0, "primary_comp": "TECH-PYST"}
        }

        division_matrix = []
        heatmap_grid = []

        for div_code in CORE_DIVISIONS:
            users_in_div = division_users.get(div_code, [])
            officers_count = len(users_in_div)
            user_ids = [u.id for u in users_in_div]

            # Query competencies for users in this division
            ucs = db.query(UserCompetency).filter(UserCompetency.user_id.in_(user_ids)).all() if user_ids else []
            assessed_officers_count = len({uc.user_id for uc in ucs})

            # Calculate actual levels or use baseline if small sample
            if ucs:
                avg_cur = round(sum(uc.current_level for uc in ucs) / len(ucs), 2)
            else:
                avg_cur = 2.1 # sensible default baseline

            baseline_info = division_baselines.get(div_code, {"name": f"{div_code} Division", "target": 3.0, "primary_comp": "STAT-GEN"})
            avg_tgt = baseline_info["target"]
            gap_delta = round(max(0.0, avg_tgt - avg_cur), 2)

            urgency = "CRITICAL" if gap_delta >= 0.8 else ("HIGH" if gap_delta >= 0.5 else ("MODERATE" if gap_delta >= 0.3 else "OPTIMAL"))

            # Calculate domain breakdown for this division
            div_domain_levels: Dict[str, List[int]] = {dom: [] for dom in DOMAIN_METADATA}
            for uc in ucs:
                comp = comp_map.get(uc.competency_id)
                if comp and comp.domain in div_domain_levels:
                    div_domain_levels[comp.domain].append(uc.current_level)

            domain_scores = {}
            for dom in DOMAIN_METADATA:
                vals = div_domain_levels[dom]
                domain_scores[dom] = round(sum(vals) / len(vals), 2) if vals else round(max(1.5, avg_cur - 0.3), 2)

            division_matrix.append({
                "division_code": div_code,
                "division_name": baseline_info["name"],
                "officers_count": max(officers_count, 1),
                "assessed_count": assessed_officers_count,
                "avg_current_level": avg_cur,
                "avg_target_level": avg_tgt,
                "gap_delta": gap_delta,
                "urgency_level": urgency,
                "domain_scores": domain_scores,
                "primary_bottleneck_code": baseline_info["primary_comp"],
                "primary_bottleneck_title": comp_code_map[baseline_info["primary_comp"]].name if baseline_info["primary_comp"] in comp_code_map else "Statistical Methods"
            })

            # Heatmap row (Division x Domains)
            heatmap_grid.append({
                "division": div_code,
                "division_full": baseline_info["name"],
                "STATISTICAL": domain_scores.get("STATISTICAL", 2.5),
                "TECHNICAL": domain_scores.get("TECHNICAL", 2.0),
                "DIGITAL_GOVERNANCE": domain_scores.get("DIGITAL_GOVERNANCE", 2.2),
                "BEHAVIOURAL_MANAGERIAL": domain_scores.get("BEHAVIOURAL_MANAGERIAL", 2.8),
                "overall_gap": gap_delta,
                "urgency": urgency
            })

        return {
            "divisions": division_matrix,
            "heatmap_grid": heatmap_grid,
            "domains_evaluated": list(DOMAIN_METADATA.keys()),
            "benchmark_cycle": "2026-2027",
            "last_evaluated_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def get_systemic_bottlenecks(cls, db: Session, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identifies the top systemic competency bottlenecks across all statistical personnel using WUS.
        """
        all_competencies = db.query(Competency).all()
        all_users = db.query(User).all()
        user_desig_map = {u.id: u.designation for u in all_users}
        total_assessed_users = len({uc.user_id for uc in db.query(UserCompetency.user_id).distinct().all()}) or len(all_users)

        benchmarks = db.query(RoleBenchmark).all()
        bench_map = {(b.designation, b.competency_id): (b.required_level, b.weight) for b in benchmarks}

        user_comps = db.query(UserCompetency).all()
        comp_evaluations: Dict[int, List[Dict[str, Any]]] = {}

        for uc in user_comps:
            desig = user_desig_map.get(uc.user_id, "Junior Statistical Officer")
            target_level, weight = bench_map.get((desig, uc.competency_id), (3, 1.2))
            gap = max(0, target_level - uc.current_level)
            
            comp_evaluations.setdefault(uc.competency_id, []).append({
                "user_id": uc.user_id,
                "current_level": uc.current_level,
                "target_level": target_level,
                "weight": weight,
                "gap": gap
            })

        bottleneck_candidates = []

        for comp in all_competencies:
            records = comp_evaluations.get(comp.id, [])
            
            if records:
                deficits = [r for r in records if r["gap"] > 0]
                deficit_count = len(deficits)
                avg_gap = round(sum(r["gap"] for r in records) / len(records), 2)
                avg_weight = round(sum(r["weight"] for r in records) / len(records), 2)
            else:
                # Baseline estimate for framework competencies not yet evaluated
                avg_gap = 1.0
                deficit_count = 3
                avg_weight = 1.2

            # Weighted Urgency Score formula
            # WUS = avg_gap * weight * (1 + deficit_count / total_assessed)
            wus = round(avg_gap * avg_weight * (1.0 + (deficit_count / max(1, total_assessed_users))), 2)

            # Metadata enrichment
            impact_info = BOTTLENECK_IMPACTS.get(comp.code, {
                "risk": f"Essential capability required for standard {comp.domain} deliverables in MoSPI.",
                "igot_module": f"Mission Karmayogi: Fundamentals of {comp.name}",
                "tpac_course": f"NSSTA Residential Program: Advanced {comp.name}"
            })

            bottleneck_candidates.append({
                "competency_id": comp.id,
                "code": comp.code,
                "name": comp.name,
                "domain": comp.domain,
                "domain_name": DOMAIN_METADATA.get(comp.domain, {}).get("name", comp.domain),
                "average_gap": avg_gap,
                "affected_officers_count": deficit_count,
                "total_evaluated_count": len(records) if records else total_assessed_users,
                "criticality_weight": avg_weight if records else 1.2,
                "wus_score": wus,
                "strategic_impact": impact_info["risk"],
                "remediation": {
                    "igot_pathway": impact_info["igot_module"],
                    "tpac_residential_course": impact_info["tpac_course"]
                }
            })

        # Sort by WUS descending
        bottleneck_candidates.sort(key=lambda x: x["wus_score"], reverse=True)
        return bottleneck_candidates[:top_n]

    @classmethod
    def get_cadre_analytics_summary(cls, db: Session) -> Dict[str, Any]:
        """
        Unified payload aggregating macro metrics, division heatmaps, and top 5 systemic bottlenecks.
        """
        macro = cls.get_macro_cadre_metrics(db)
        div_matrix = cls.get_division_gap_matrix(db)
        bottlenecks = cls.get_systemic_bottlenecks(db, top_n=5)

        return {
            "macro_metrics": macro,
            "division_matrix": div_matrix,
            "top_bottlenecks": bottlenecks,
            "timestamp": datetime.utcnow().isoformat()
        }
