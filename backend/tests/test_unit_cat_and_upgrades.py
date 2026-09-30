import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.competency import Competency, UserCompetency
from app.models.assessment import Quiz, Question, QuizAttempt
from app.schemas.competency import SupervisorCalibrateRequest
from app.api.competencies import supervisor_calibrate
from app.api.assessments import submit_quiz
from app.schemas.assessment import QuizSubmitRequest

def test_quiz_pass_triggers_competency_promotion(db_session: Session):
    """
    Verifies that scoring >= pass_percentage on a competency quiz
    promotes the officer's rubric level, updates assessed_via to 'QUIZ',
    and recalibrates the confidence score.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    comp = db_session.query(Competency).filter(Competency.code == "STAT-PRICE").first()
    assert user is not None and comp is not None

    # Check initial level for STAT-PRICE (seeded at L2 in conftest)
    uc = db_session.query(UserCompetency).filter(
        UserCompetency.user_id == user.id,
        UserCompetency.competency_id == comp.id
    ).first()
    assert uc is not None
    initial_level = uc.current_level
    assert initial_level == 2

    # Create a quiz targeting Level 3 with pass_percentage = 75.0
    quiz = Quiz(
        title="CPI & Price Index Assessment",
        competency_code="STAT-PRICE",
        target_level=3,
        total_questions=2,
        pass_percentage=75.0,
        is_adaptive=True
    )
    db_session.add(quiz)
    db_session.flush()

    q1 = Question(
        quiz_id=quiz.id,
        question_text="What index formula does MoSPI use for elementary aggregate price compilation in CPI?",
        options=["Laspeyres Index", "Paasche Index", "Jevons Geometric Mean Index", "Fisher Ideal Index"],
        correct_option_index=2,
        explanation="MoSPI utilizes the Jevons elementary formula for geometric aggregation.",
        citation="MoSPI CPI Manual Section 4.2",
        blooms_level="UNDERSTAND",
        difficulty_level=2
    )
    q2 = Question(
        quiz_id=quiz.id,
        question_text="In CPI basket revision, what survey provides household consumption expenditure weights?",
        options=["ASI Survey", "Periodic Labour Force Survey (PLFS)", "Household Consumption Expenditure Survey (HCES)", "Time Use Survey"],
        correct_option_index=2,
        explanation="HCES provides household weighting diagrams.",
        citation="MoSPI CPI Technical Note",
        blooms_level="APPLY",
        difficulty_level=3
    )
    db_session.add_all([q1, q2])
    db_session.flush()

    # Simulate passing attempt: both answers correct (100% score)
    req = QuizSubmitRequest(
        user_answers={str(q1.id): 2, str(q2.id): 2},
        time_taken_seconds=120
    )

    result = submit_quiz(id=quiz.id, req=req, db=db_session, current_user=user)
    assert result.passed is True
    assert result.percentage == 100.0
    assert result.competency_promoted is True
    assert result.new_level == 3

    # Verify database state after commit
    db_session.refresh(uc)
    assert uc.current_level == 3
    assert uc.assessed_via == "QUIZ"
    assert uc.confidence_score >= 0.90

def test_quiz_fail_leaves_level_unchanged(db_session: Session):
    """
    Verifies that scoring below pass_percentage does NOT promote the officer's level.
    """
    user = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    comp = db_session.query(Competency).filter(Competency.code == "STAT-NAS").first()
    assert user is not None and comp is not None

    uc = db_session.query(UserCompetency).filter(
        UserCompetency.user_id == user.id,
        UserCompetency.competency_id == comp.id
    ).first()
    initial_level = uc.current_level

    quiz = Quiz(
        title="National Accounts L3 Assessment",
        competency_code="STAT-NAS",
        target_level=3,
        total_questions=2,
        pass_percentage=75.0
    )
    db_session.add(quiz)
    db_session.flush()

    q1 = Question(
        quiz_id=quiz.id,
        question_text="What is the production boundary in SNA 2008?",
        options=["A", "B", "C", "D"],
        correct_option_index=0,
        explanation="Production boundary definition under SNA 2008.",
        citation="SNA 2008 Chapter 6"
    )
    q2 = Question(
        quiz_id=quiz.id,
        question_text="How is GVA at basic prices derived from factor cost?",
        options=["A", "B", "C", "D"],
        correct_option_index=1,
        explanation="GVA basic prices = GVA factor cost + production taxes less production subsidies.",
        citation="MoSPI NAS Methodology Note"
    )
    db_session.add_all([q1, q2])
    db_session.flush()

    # Select wrong answers -> 0% score
    req = QuizSubmitRequest(
        user_answers={str(q1.id): 3, str(q2.id): 3},
        time_taken_seconds=90
    )

    result = submit_quiz(id=quiz.id, req=req, db=db_session, current_user=user)
    assert result.passed is False
    assert result.competency_promoted is False

    db_session.refresh(uc)
    assert uc.current_level == initial_level

def test_supervisor_calibrate_upgrades_competency(db_session: Session):
    """
    Tests supervisor calibration workflow (POST /api/competencies/supervisor-calibrate)
    authorizing Division Heads to evaluate and upgrade subordinate officers.
    """
    jso = db_session.query(User).filter(User.email == "jso.sharma@mospi.gov.in").first()
    ad = db_session.query(User).filter(User.email == "ad.verma@mospi.gov.in").first()
    comp = db_session.query(Competency).filter(Competency.code == "TECH-PYST").first()
    assert jso is not None and ad is not None and comp is not None

    req = SupervisorCalibrateRequest(
        subordinate_id=jso.id,
        competency_id=comp.id,
        calibrated_level=3,
        justification="Demonstrated proficiency with Pandas survey scripts during NSS validation."
    )

    res = supervisor_calibrate(req=req, db=db_session, current_user=ad)
    assert res.success is True
    assert res.new_level == 3
    assert res.competency_code == "TECH-PYST"

    uc = db_session.query(UserCompetency).filter(
        UserCompetency.user_id == jso.id,
        UserCompetency.competency_id == comp.id
    ).first()
    assert uc.current_level == 3
    assert uc.assessed_via == "SUPERVISOR"
