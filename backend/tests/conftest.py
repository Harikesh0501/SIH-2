import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.models.user import User, CadreType, UserRole
from app.models.competency import Competency, CompetencyLevel, RoleBenchmark, UserCompetency
from app.models.course import Course, Enrollment, EnrollmentStatus
from app.models.passport import DigitalCredential

# In-memory SQLite with StaticPool preserves the same in-memory DB across all threads/sessions
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # 1. Seed Core MoSPI Competencies (All 4 Domains)
    comps_data = [
        # Domain 1: STATISTICAL
        ("STAT-SURV", "Survey Design & Sampling Methods (NSS)", "STATISTICAL", 1.4),
        ("STAT-NAS", "National Accounts & GVA/GDP (SNA 2008)", "STATISTICAL", 1.5),
        ("STAT-PRICE", "Price Statistics, CPI & Inflation Indices", "STATISTICAL", 1.3),
        ("STAT-DQAF", "Data Quality Assurance Framework (DQAF)", "STATISTICAL", 1.4),
        # Domain 2: TECHNICAL
        ("TECH-PYST", "Python for Official Statistics & Pandas", "TECHNICAL", 1.5),
        ("TECH-CAPI", "CAPI / Mobile Computer Assisted Interviewing", "TECHNICAL", 1.2),
        ("TECH-RSTA", "R for Official Statistics & Econometrics", "TECHNICAL", 1.3),
        ("TECH-DBQL", "Relational Databases & SQL for Civil Servants", "TECHNICAL", 1.2),
        # Domain 3: DIGITAL_GOVERNANCE
        ("GOV-OPENDATA", "Open Data Policy & Microdata Dissemination", "DIGITAL_GOVERNANCE", 1.2),
        ("GOV-METADATA", "Statistical Metadata & SDMX Standards", "DIGITAL_GOVERNANCE", 1.1),
        # Domain 4: BEHAVIOURAL_MANAGERIAL
        ("MGMT-ETHC", "Professional Ethics in Official Statistics", "BEHAVIOURAL_MANAGERIAL", 1.4),
        ("MGMT-LEAD", "Field Team Leadership & Crisis Resolution", "BEHAVIOURAL_MANAGERIAL", 1.2),
    ]

    comp_objects = {}
    for code, name, domain, default_weight in comps_data:
        comp = Competency(code=code, name=name, domain=domain, description=f"Official MoSPI competency for {name}")
        db.add(comp)
        db.flush()
        comp_objects[code] = comp

        # Add 5 levels
        for lvl in range(1, 6):
            cl = CompetencyLevel(
                competency_id=comp.id,
                level=lvl,
                descriptor=f"Demonstrates Level {lvl} mastery in {name}."
            )
            db.add(cl)

    # 2. Seed Role Benchmarks for "Junior Statistical Officer" (JSO) & "Assistant Director" (AD)
    jso_benchmarks = [
        ("STAT-SURV", 3, 1.4),
        ("STAT-NAS", 2, 1.2),
        ("STAT-PRICE", 3, 1.3),
        ("STAT-DQAF", 3, 1.4),
        ("TECH-PYST", 3, 1.5),
        ("TECH-CAPI", 3, 1.2),
        ("MGMT-ETHC", 3, 1.3),
    ]
    for code, req_lvl, w in jso_benchmarks:
        if code in comp_objects:
            rb = RoleBenchmark(
                designation="Junior Statistical Officer",
                competency_id=comp_objects[code].id,
                required_level=req_lvl,
                weight=w,
                is_mandatory=True
            )
            db.add(rb)

    ad_benchmarks = [
        ("STAT-SURV", 4, 1.4),
        ("STAT-NAS", 4, 1.6),
        ("STAT-PRICE", 4, 1.3),
        ("STAT-DQAF", 4, 1.4),
        ("TECH-PYST", 3, 1.3),
        ("MGMT-ETHC", 4, 1.4),
    ]
    for code, req_lvl, w in ad_benchmarks:
        if code in comp_objects:
            rb = RoleBenchmark(
                designation="Assistant Director",
                competency_id=comp_objects[code].id,
                required_level=req_lvl,
                weight=w,
                is_mandatory=True
            )
            db.add(rb)

    # 3. Seed Demo Users
    hashed_pwd = get_password_hash("Password@123")

    # JSO Pooja Sharma
    jso_user = User(
        id=4,
        email="jso.sharma@mospi.gov.in",
        full_name="Pooja Sharma",
        hashed_password=hashed_pwd,
        role=UserRole.LEARNER.value,
        designation="Junior Statistical Officer",
        cadre=CadreType.SSS.value,
        division="FOD",
        organization="Ministry of Statistics & Programme Implementation (MoSPI)",
        experience_years=4,
        education="M.Sc. Statistics, Delhi University"
    )
    db.add(jso_user)

    # AD Rajesh Verma (Supervisor)
    ad_user = User(
        id=5,
        email="ad.verma@mospi.gov.in",
        full_name="Rajesh Verma",
        hashed_password=hashed_pwd,
        role=UserRole.SUPERVISOR.value,
        designation="Assistant Director",
        cadre=CadreType.ISS.value,
        division="NAD",
        organization="Ministry of Statistics & Programme Implementation (MoSPI)",
        experience_years=9,
        education="M.Stat, Indian Statistical Institute (ISI)"
    )
    db.add(ad_user)

    # Admin Alok Mathur
    admin_user = User(
        id=7,
        email="admin.cadre@mospi.gov.in",
        full_name="Alok Mathur",
        hashed_password=hashed_pwd,
        role=UserRole.ADMIN.value,
        designation="Director",
        cadre=CadreType.ISS.value,
        division="Cadre Administration & Policy",
        organization="Ministry of Statistics & Programme Implementation (MoSPI)",
        experience_years=18,
        education="Ph.D. Econometrics, Delhi School of Economics"
    )
    db.add(admin_user)
    db.flush()

    # Set supervisor relation
    jso_user.supervisor_id = ad_user.id

    # 4. Seed User Competencies for Pooja Sharma (JSO)
    # L3 in STAT-SURV (met), L2 in STAT-NAS (gap 0 for JSO L2 target, or gap 1 for target 3), L2 in TECH-PYST (gap 1)
    jso_competency_evals = [
        ("STAT-SURV", 3, "QUIZ", 0.92),
        ("STAT-NAS", 2, "IGOT", 0.85),
        ("STAT-PRICE", 2, "SUPERVISOR", 0.88),
        ("STAT-DQAF", 3, "QUIZ", 0.90),
        ("TECH-PYST", 2, "QUIZ", 0.82),
        ("TECH-CAPI", 4, "SUPERVISOR", 0.95),
        ("MGMT-ETHC", 3, "SUPERVISOR", 0.94),
    ]
    for code, cur_lvl, source, conf in jso_competency_evals:
        if code in comp_objects:
            uc = UserCompetency(
                user_id=jso_user.id,
                competency_id=comp_objects[code].id,
                current_level=cur_lvl,
                assessed_via=source,
                confidence_score=conf
            )
            db.add(uc)

    # 5. Seed Test Courses (iGOT and NSSTA TPAC)
    c1 = Course(
        id=1,
        external_id="IGOT-STAT-001",
        title="National Sample Survey (NSS) Fundamentals & Field Concepts",
        source="IGOT_KARMAYOGI",
        delivery_mode="Self-Paced Digital",
        description="Core digital module covering sampling frames and stratified estimation.",
        provider="iGOT Karmayogi / MoSPI",
        duration_hours=12.5,
        target_competencies=["STAT-SURV"],
        target_level=2,
        is_active=True
    )
    c2 = Course(
        id=2,
        external_id="NSSTA-TPAC-001",
        title="Advanced CAPI Survey Deployment & Tablet Enumeration Workshop",
        source="NSSTA_TPAC",
        delivery_mode="Residential Workshop",
        description="Residential workshop for CAPI survey operations and tablet data collection.",
        provider="NSSTA Greater Noida",
        duration_hours=36.0,
        target_competencies=["STAT-SURV", "TECH-CAPI"],
        target_level=3,
        is_active=True
    )
    c3 = Course(
        id=3,
        external_id="NSSTA-TPAC-003",
        title="Modern Python for Official Statistics & Automated Data Pipelines",
        source="NSSTA_TPAC",
        delivery_mode="Hands-on Lab Bootcamp",
        description="Hands-on computing lab covering Pandas, data engineering, and automation.",
        provider="NSSTA Greater Noida",
        duration_hours=40.0,
        target_competencies=["TECH-PYST"],
        target_level=3,
        is_active=True
    )
    db.add_all([c1, c2, c3])
    db.flush()

    # 6. Seed a completed enrollment for c1
    en = Enrollment(
        user_id=jso_user.id,
        course_id=c1.id,
        status=EnrollmentStatus.COMPLETED.value,
        progress_percentage=100.0,
        certificate_id="CERT-KY-IGOT-STAT-001-0004"
    )
    db.add(en)

    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    """Provides a transactional session that rolls back after each test function"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def jso_token():
    return create_access_token(data={"sub": "jso.sharma@mospi.gov.in"})

@pytest.fixture
def ad_token():
    return create_access_token(data={"sub": "ad.verma@mospi.gov.in"})

@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": "admin.cadre@mospi.gov.in"})

@pytest.fixture
def auth_headers_jso(jso_token):
    return {"Authorization": f"Bearer {jso_token}"}

@pytest.fixture
def auth_headers_ad(ad_token):
    return {"Authorization": f"Bearer {ad_token}"}

@pytest.fixture
def auth_headers_admin(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
