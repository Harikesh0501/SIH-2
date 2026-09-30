import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.competency import Competency, RoleBenchmark, UserCompetency
from app.services.gap_analyzer import CompetencyGapAnalyzer

def test_gap_calculation_met_and_deficit(db_session: Session):
    """
    Verifies that competencies at or above benchmark level report gap=0 and status='ON_TRACK' or 'EXCEEDS',
    while competencies below benchmark level report accurate gap delta and 'MODERATE_GAP' or 'CRITICAL_GAP'.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    assert user is not None

    gap_analysis = CompetencyGapAnalyzer.analyze_gaps(db_session, user)
    assert gap_analysis is not None

    comp_dict = {c.code: c for c in gap_analysis.all_competencies}

    # In conftest: STAT-SURV current_level = 3, JSO benchmark = 3 -> gap 0, ON_TRACK
    assert "STAT-SURV" in comp_dict
    surv_comp = comp_dict["STAT-SURV"]
    assert surv_comp.current_level == 3
    assert surv_comp.required_level == 3
    assert surv_comp.gap == 0
    assert surv_comp.status in ["ON_TRACK", "EXCEEDS"]

    # In conftest: TECH-PYST current_level = 2, JSO benchmark = 3 -> gap 1, MODERATE_GAP
    assert "TECH-PYST" in comp_dict
    pyst_comp = comp_dict["TECH-PYST"]
    assert pyst_comp.current_level == 2
    assert pyst_comp.required_level == 3
    assert pyst_comp.gap == 1
    assert pyst_comp.status == "MODERATE_GAP"
    assert pyst_comp.urgency_score > 0.0

def test_weighted_urgency_score_formula(db_session: Session):
    """
    Verifies that urgency score obeys the mathematical formulation:
    Urgency = gap * weight * (1.5 if is_mandatory else 1.0)
    and higher weights with larger gaps result in proportionally higher urgency scores.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    gap_analysis = CompetencyGapAnalyzer.analyze_gaps(db_session, user)

    for item in gap_analysis.all_competencies:
        if item.gap > 0:
            assert item.urgency_score > 0.0
            rb = db_session.query(RoleBenchmark).filter(
                RoleBenchmark.designation == user.designation,
                RoleBenchmark.competency_id == item.competency_id
            ).first()
            if rb:
                expected_urgency = round(item.gap * rb.weight * (1.5 if rb.is_mandatory else 1.0), 2)
                assert item.urgency_score == expected_urgency
        else:
            assert item.urgency_score == 0.0

def test_overall_readiness_percentage_bounds(db_session: Session):
    """
    Verifies that overall readiness percentage is always bounded between 0.0% and 100.0%.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    gap_analysis = CompetencyGapAnalyzer.analyze_gaps(db_session, user)

    assert 0.0 <= gap_analysis.overall_readiness_percentage <= 100.0
    # JSO Pooja Sharma has multiple met competencies, readiness should be high
    assert gap_analysis.overall_readiness_percentage > 50.0

def test_career_simulation_target_role(db_session: Session):
    """
    Tests career progression simulator projecting future competency requirements
    when transitioning from JSO to 'Assistant Director'.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    target_role = "Assistant Director"

    sim = CompetencyGapAnalyzer.simulate_career_pathway(db_session, user, target_role)
    assert sim is not None
    assert sim.target_designation == target_role
    assert 0.0 <= sim.readiness_percentage <= 100.0

    # AD requires L4 in STAT-SURV and STAT-NAS. JSO Pooja currently has L3 and L2.
    # Therefore, new competency gaps must be diagnosed.
    assert len(sim.projected_gaps) > 0

    gap_codes = [g.code for g in sim.projected_gaps]
    assert "STAT-NAS" in gap_codes or "STAT-SURV" in gap_codes

    # Upskilling roadmap must contain prioritized stages
    assert len(sim.recommended_pathway_summary) > 0
