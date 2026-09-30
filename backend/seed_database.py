import os
import sys
import json
import uuid
from datetime import datetime

# Configure safe UTF-8 output for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole, CadreType
from app.models.competency import (
    Competency,
    CompetencyLevel,
    RoleBenchmark,
    UserCompetency,
)
from app.models.course import Course, CourseSource, DeliveryMode, Enrollment, EnrollmentStatus
from app.models.assessment import (
    LearningMaterial,
    MaterialChunk,
    Quiz,
    Question,
    QuizAttempt,
    BloomsLevel,
)
from app.models.passport import DigitalCredential
from app.models.chat import ChatMessage
from app.data.framework_loader import load_competency_framework, load_role_benchmarks

def seed():
    print("=" * 60)
    print("[*] KARMAYOGI SANKHYIKI - DATABASE SEEDING ENGINE")
    print("=" * 60)

    # 1. Reset and Recreate Tables
    print("[1/7] Initializing clean database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 2. Seed Competencies & Levels
        print("[2/7] Seeding Official Statistical Competency Framework...")
        framework_data = load_competency_framework()
        competencies_map = {}

        for comp_data in framework_data.get("competencies", []):
            comp = Competency(
                code=comp_data["code"],
                name=comp_data["name"],
                domain=comp_data["domain"],
                description=comp_data["description"],
            )
            db.add(comp)
            db.flush()
            competencies_map[comp.code] = comp

            # Seed 5 Levels for this competency
            for lvl_data in comp_data.get("levels", []):
                lvl = CompetencyLevel(
                    competency_id=comp.id,
                    level=lvl_data["level"],
                    descriptor=lvl_data["descriptor"],
                    knowledge_indicators=lvl_data.get("knowledge_indicators", []),
                    skill_indicators=lvl_data.get("skill_indicators", []),
                )
                db.add(lvl)

        print(f"      -> Successfully seeded {len(competencies_map)} competencies across 4 official domains.")

        # 3. Seed Role Benchmarks
        print("[3/7] Seeding Cadre Role Benchmark Matrices...")
        role_benchmarks_data = load_role_benchmarks()
        benchmark_count = 0

        for role_data in role_benchmarks_data:
            designation = role_data["designation"]
            for bm in role_data.get("benchmarks", []):
                comp_code = bm["competency_code"]
                comp = competencies_map.get(comp_code)
                if comp:
                    rb = RoleBenchmark(
                        designation=designation,
                        competency_id=comp.id,
                        required_level=bm["required_level"],
                        is_mandatory=bm.get("is_mandatory", True),
                        weight=bm.get("weight", 1.0),
                    )
                    db.add(rb)
                    benchmark_count += 1

        print(f"      -> Successfully seeded {benchmark_count} benchmark rules across 5 designations.")

        # 4. Seed Official Users & Personas
        print("[4/7] Seeding MoSPI Personas & Civil Service Cadre Profiles...")
        default_pwd = get_password_hash("Password@123")

        # Admin / Ministry Leadership
        admin_user = User(
            email="admin.cadre@mospi.gov.in",
            hashed_password=default_pwd,
            full_name="Alok Mathur",
            cadre=CadreType.ISS.value,
            designation="Director / Deputy Director General",
            division="Coordination & Cadre Administration",
            organization="Ministry of Statistics & Programme Implementation (MoSPI)",
            experience_years=22,
            education="Ph.D. in Econometrics & Statistical Policy",
            role=UserRole.ADMIN.value,
        )
        db.add(admin_user)
        db.flush()

        # Faculty / NSSTA Trainer
        faculty_user = User(
            email="faculty.nssta@nic.in",
            hashed_password=default_pwd,
            full_name="Dr. Sunita Rao",
            cadre=CadreType.ISS.value,
            designation="Director / Senior Faculty",
            division="National Statistical Systems Training Academy (NSSTA)",
            organization="NSSTA Greater Noida, MoSPI",
            experience_years=18,
            education="Ph.D. in Sampling & Survey Methodology",
            role=UserRole.TRAINER.value,
        )
        db.add(faculty_user)
        db.flush()

        # Assistant Director (Learner / Supervisor)
        ad_user = User(
            email="ad.verma@mospi.gov.in",
            hashed_password=default_pwd,
            full_name="Rajesh Verma",
            cadre=CadreType.ISS.value,
            designation="Assistant Director",
            division="National Accounts Division (NAD)",
            organization="Central Statistics Office (CSO), MoSPI",
            supervisor_id=admin_user.id,
            experience_years=6,
            education="Master of Science in Statistics (ISI Kolkata)",
            role=UserRole.SUPERVISOR.value,
        )
        db.add(ad_user)
        db.flush()

        # Junior Statistical Officer (Learner)
        jso_user = User(
            email="jso.sharma@mospi.gov.in",
            hashed_password=default_pwd,
            full_name="Pooja Sharma",
            cadre=CadreType.SSS.value,
            designation="Junior Statistical Officer",
            division="Field Operations Division (FOD)",
            organization="National Statistical Office (NSO), Regional Office Jaipur",
            supervisor_id=ad_user.id,
            experience_years=2,
            education="M.Sc. in Applied Statistics & Operations Research",
            role=UserRole.LEARNER.value,
        )
        db.add(jso_user)
        db.flush()

        # Additional SSS officers for Supervisor Team Matrix
        officer2 = User(
            email="sso.patel@mospi.gov.in",
            hashed_password=default_pwd,
            full_name="Bhavesh Patel",
            cadre=CadreType.SSS.value,
            designation="Senior Statistical Officer",
            division="Economic Statistics Division (ESD)",
            organization="MoSPI",
            supervisor_id=ad_user.id,
            experience_years=7,
            education="M.A. in Economics",
            role=UserRole.LEARNER.value,
        )
        officer3 = User(
            email="jso.singh@mospi.gov.in",
            hashed_password=default_pwd,
            full_name="Aman Singh",
            cadre=CadreType.SSS.value,
            designation="Junior Statistical Officer",
            division="Data Processing Division (DPD)",
            organization="MoSPI",
            supervisor_id=ad_user.id,
            experience_years=3,
            education="B.Sc. Statistics",
            role=UserRole.LEARNER.value,
        )
        db.add_all([officer2, officer3])
        db.flush()

        # Seed User Competency Baselines
        # Pooja Sharma: Strong in Survey (3), weak in Price (1) and Python (1)
        jso_comps = [
            ("STAT-SURV", 3, "SUPERVISOR", 0.9),
            ("STAT-PRICE", 1, "SELF", 0.5), # CRITICAL GAP
            ("STAT-DQAF", 2, "SELF", 0.7),
            ("TECH-PYST", 1, "SELF", 0.4),  # CRITICAL GAP
            ("TECH-DBQL", 2, "SELF", 0.6),
            ("GOV-CYBER", 2, "SELF", 0.8),
            ("MGMT-ETHC", 3, "SUPERVISOR", 0.95),
            ("STAT-LABOUR", 2, "SELF", 0.6),
        ]
        for code, level, assessed_via, conf in jso_comps:
            comp = competencies_map.get(code)
            if comp:
                db.add(UserCompetency(
                    user_id=jso_user.id,
                    competency_id=comp.id,
                    current_level=level,
                    assessed_via=assessed_via,
                    confidence_score=conf,
                ))

        # Rajesh Verma competencies
        ad_comps = [
            ("STAT-NAS", 3, "SUPERVISOR", 0.85),
            ("STAT-SDG", 2, "SELF", 0.6),
            ("STAT-PRICE", 3, "SELF", 0.75),
            ("TECH-AIML", 1, "SELF", 0.4),  # GAP
            ("TECH-VIZ", 3, "SELF", 0.8),
            ("GOV-DPDP", 3, "SELF", 0.7),
            ("MGMT-COMM", 3, "SELF", 0.8),
            ("MGMT-LEAD", 2, "SELF", 0.6),
        ]
        for code, level, assessed_via, conf in ad_comps:
            comp = competencies_map.get(code)
            if comp:
                db.add(UserCompetency(
                    user_id=ad_user.id,
                    competency_id=comp.id,
                    current_level=level,
                    assessed_via=assessed_via,
                    confidence_score=conf,
                ))

        # Bhavesh Patel & Aman Singh competencies
        for code, level in [("STAT-SURV", 4), ("STAT-LABOUR", 3), ("TECH-PYST", 3)]:
            c = competencies_map.get(code)
            if c:
                db.add(UserCompetency(user_id=officer2.id, competency_id=c.id, current_level=level))
        for code, level in [("TECH-DBQL", 3), ("STAT-PRICE", 2), ("TECH-PYST", 2)]:
            c = competencies_map.get(code)
            if c:
                db.add(UserCompetency(user_id=officer3.id, competency_id=c.id, current_level=level))

        print(f"      -> Successfully seeded 6 personnel records with realistic competency baselines.")

        # 5. Seed iGOT Karmayogi Courses & NSSTA TPAC Training Programmes
        print("[5/7] Seeding Course Catalogs (iGOT Karmayogi & NSSTA TPAC)...")

        courses_data = [
            # Track A: iGOT Karmayogi Courses
            {
                "external_id": "IGOT-STAT-101",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Introduction to Consumer Price Index (CPI) Compilation",
                "description": "Comprehensive self-paced e-learning module covering CPI item baskets, price quotation collection, Laspeyres formula, and base year revisions.",
                "provider": "Karmayogi Bharat & MoSPI",
                "duration_hours": 3.5,
                "delivery_mode": DeliveryMode.ONLINE_SELF_PACED.value,
                "target_competencies": ["STAT-PRICE"],
                "target_level": 2,
                "rating": 4.9,
                "thumbnail_url": "/thumbnails/cpi_course.jpg",
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-STAT-101",
            },
            {
                "external_id": "IGOT-STAT-102",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Elementary Aggregations & Imputation in Price Statistics",
                "description": "Advanced calculation techniques for geometric mean price relatives (Jevons), carry-forward, and cell-mean imputation methods for missing market quotes.",
                "provider": "Karmayogi Bharat & ESD MoSPI",
                "duration_hours": 2.0,
                "target_competencies": ["STAT-PRICE", "STAT-DQAF"],
                "target_level": 3,
                "rating": 4.8,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-STAT-102",
            },
            {
                "external_id": "IGOT-TECH-201",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Python for Statistical Automation & Data Wrangling",
                "description": "Practical hands-on training with Pandas, NumPy, and automated data cleaning scripts for official survey datasets.",
                "provider": "Karmayogi Bharat & NIC",
                "duration_hours": 6.0,
                "delivery_mode": DeliveryMode.ONLINE_SELF_PACED.value,
                "target_competencies": ["TECH-PYST"],
                "target_level": 2,
                "rating": 4.85,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-TECH-201",
            },
            {
                "external_id": "IGOT-TECH-202",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Advanced Python for Large-Scale Microdata Analysis",
                "description": "Vectorized computations, processing multi-round NSS datasets, applying multiplier weights, and statistical modeling with Statsmodels.",
                "provider": "Karmayogi Bharat & MoSPI",
                "duration_hours": 8.0,
                "target_competencies": ["TECH-PYST", "TECH-AIML"],
                "target_level": 3,
                "rating": 4.9,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-TECH-202",
            },
            {
                "external_id": "IGOT-STAT-103",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "National Accounts Fundamentals: GVA at Basic Prices vs GDP",
                "description": "Mastering the SNA 2008 framework, difference between product and production taxes, and sectoral growth compilation.",
                "provider": "Karmayogi Bharat & NAD MoSPI",
                "duration_hours": 4.0,
                "target_competencies": ["STAT-NAS"],
                "target_level": 2,
                "rating": 4.92,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-STAT-103",
            },
            {
                "external_id": "IGOT-STAT-104",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Supply and Use Tables (SUT) & GDP Reconciliation",
                "description": "In-depth guide to balancing macroeconomic supply and use matrices, resolving statistical discrepancy, and intermediate consumption.",
                "provider": "Karmayogi Bharat & NAD MoSPI",
                "duration_hours": 5.0,
                "target_competencies": ["STAT-NAS"],
                "target_level": 3,
                "rating": 4.88,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-STAT-104",
            },
            {
                "external_id": "IGOT-GOV-301",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Digital Personal Data Protection (DPDP) Act 2023 for Public Servants",
                "description": "Understanding Data Fiduciary duties, respondent privacy, de-identification techniques, and statistical disclosure controls.",
                "provider": "Karmayogi Bharat & MeitY",
                "duration_hours": 2.5,
                "target_competencies": ["GOV-DPDP"],
                "target_level": 2,
                "rating": 4.75,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-GOV-301",
            },
            {
                "external_id": "IGOT-STAT-105",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Periodic Labour Force Survey (PLFS): Concepts & Measurement",
                "description": "Usual Status (UPS+SS), Current Weekly Status (CWS), calculating LFPR, WPR, and UR according to official NSO standards.",
                "provider": "Karmayogi Bharat & SDRD MoSPI",
                "duration_hours": 3.0,
                "target_competencies": ["STAT-LABOUR"],
                "target_level": 2,
                "rating": 4.8,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-STAT-105",
            },
            {
                "external_id": "IGOT-TECH-203",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "Geospatial Mapping & QGIS in Official Surveys",
                "description": "Thematic mapping, integrating Bhuvan spatial data, creating block boundaries for FOD survey teams.",
                "provider": "Karmayogi Bharat & ISRO",
                "duration_hours": 4.5,
                "target_competencies": ["TECH-GIS"],
                "target_level": 2,
                "rating": 4.82,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-TECH-203",
            },
            {
                "external_id": "IGOT-MGMT-401",
                "source": CourseSource.IGOT_KARMAYOGI.value,
                "title": "UN Fundamental Principles of Official Statistics & Ethics",
                "description": "Professional independence, confidentiality preservation, and maintaining public trust in official government figures.",
                "provider": "Karmayogi Bharat & NSSTA",
                "duration_hours": 2.0,
                "target_competencies": ["MGMT-ETHC"],
                "target_level": 3,
                "rating": 4.95,
                "course_url": "https://igotkarmayogi.gov.in/app/explore/course/IGOT-MGMT-401",
            },

            # Track B: NSSTA TPAC Approved In-Person Residential Programmes
            {
                "external_id": "TPAC-2026-RES-01",
                "source": CourseSource.NSSTA_TPAC.value,
                "title": "National Workshop on Price Indices, Inflation & HCES Revisions",
                "description": "Two-week intensive residential training program at NSSTA Greater Noida for SSS/ISS officers on CPI base revision, scanner data, and outlet sampling.",
                "provider": "NSSTA Greater Noida (TPAC Approved)",
                "duration_hours": 36.0,
                "delivery_mode": DeliveryMode.RESIDENTIAL_IN_PERSON.value,
                "location": "NSSTA Campus, Plot No. 22, Knowledge Park-II, Greater Noida",
                "batch_start_date": "15th November 2026",
                "batch_capacity": 35,
                "target_competencies": ["STAT-PRICE", "STAT-DQAF"],
                "target_level": 3,
                "rating": 4.96,
                "course_url": "https://mospi.gov.in/nssta/training-calendar/2026/RES-01",
            },
            {
                "external_id": "TPAC-2026-RES-02",
                "source": CourseSource.NSSTA_TPAC.value,
                "title": "Executive Workshop on Advanced Macroeconomic Accounts (SNA 2025)",
                "description": "Residential capacity building program on Supply-Use Tables, digital economy estimation, and financial balance sheets for Assistant Directors and Deputy Directors.",
                "provider": "NSSTA Greater Noida & ISI Delhi",
                "duration_hours": 40.0,
                "delivery_mode": DeliveryMode.RESIDENTIAL_IN_PERSON.value,
                "location": "NSSTA Campus, Greater Noida",
                "batch_start_date": "1st December 2026",
                "batch_capacity": 30,
                "target_competencies": ["STAT-NAS", "STAT-SDG"],
                "target_level": 4,
                "rating": 4.98,
                "course_url": "https://mospi.gov.in/nssta/training-calendar/2026/RES-02",
            },
            {
                "external_id": "TPAC-2026-RES-03",
                "source": CourseSource.NSSTA_TPAC.value,
                "title": "Modern Survey Sampling Design, SAE & Non-Sampling Error Mitigation",
                "description": "Comprehensive 10-day hands-on residential training on multi-stage PPS designs, Small Area Estimation, and sub-sample variance computation.",
                "provider": "NSSTA Greater Noida",
                "duration_hours": 30.0,
                "delivery_mode": DeliveryMode.RESIDENTIAL_IN_PERSON.value,
                "location": "NSSTA Campus, Greater Noida",
                "batch_start_date": "10th January 2027",
                "batch_capacity": 40,
                "target_competencies": ["STAT-SURV", "STAT-DQAF"],
                "target_level": 4,
                "rating": 4.92,
                "course_url": "https://mospi.gov.in/nssta/training-calendar/2026/RES-03",
            },
            {
                "external_id": "TPAC-2026-RES-04",
                "source": CourseSource.NSSTA_TPAC.value,
                "title": "Applied AI, Machine Learning & Remote Sensing in Official Statistics",
                "description": "Joint technical residential workshop with ISRO and IIT Delhi on satellite crop estimation, automated imputation algorithms, and NLP for survey codes.",
                "provider": "NSSTA Greater Noida & ISRO",
                "duration_hours": 35.0,
                "delivery_mode": DeliveryMode.BLENDED.value,
                "location": "NSSTA Campus, Greater Noida",
                "batch_start_date": "20th January 2027",
                "batch_capacity": 30,
                "target_competencies": ["TECH-AIML", "TECH-GIS", "TECH-PYST"],
                "target_level": 3,
                "rating": 4.94,
                "course_url": "https://mospi.gov.in/nssta/training-calendar/2026/RES-04",
            },
            {
                "external_id": "TPAC-2026-RTC-01",
                "source": CourseSource.NSSTA_TPAC.value,
                "title": "Regional Training Programme on Data Scrutiny, Validation & DPDP Act",
                "description": "Five-day intensive regional course at RTC Kolkata for Eastern Zone field investigators and SSS supervisors on automated validation scripts and privacy.",
                "provider": "Regional Training Center (RTC) Kolkata, NSSTA",
                "duration_hours": 25.0,
                "delivery_mode": DeliveryMode.RESIDENTIAL_IN_PERSON.value,
                "location": "RTC Kolkata, Salt Lake City",
                "batch_start_date": "5th February 2027",
                "batch_capacity": 45,
                "target_competencies": ["STAT-DQAF", "GOV-DPDP"],
                "target_level": 3,
                "rating": 4.86,
                "course_url": "https://mospi.gov.in/nssta/rtc-kolkata/2026/RTC-01",
            }
        ]

        for c_data in courses_data:
            course = Course(**c_data)
            db.add(course)

        db.flush()
        print(f"      -> Successfully seeded {len(courses_data)} courses across iGOT Karmayogi and NSSTA TPAC tracks.")

        # 6. Seed Sample Learning Materials, Chunks, Quizzes & Questions
        print("[6/7] Ingesting Official MoSPI Learning Materials & Generating Seed Quizzes...")

        sample_materials = [
            {
                "title": "MoSPI Manual on Consumer Price Index (Base 2012=100)",
                "description": "Official CSO / NSO methodological guidelines on commodity basket weighting, price quotation collection, Laspeyres index compilation, and missing quote imputation.",
                "filename": "cpi_manual_methodology_excerpt.txt",
                "file_type": "txt",
                "file_path": "sample_data/cpi_manual_methodology_excerpt.txt",
                "competency_code": "STAT-PRICE",
                "target_level": 2,
                "quiz_title": "Benchmark Assessment: Consumer Price Index (CPI) Compilation & Aggregation",
                "questions": [
                    {
                        "question_text": "Which index compilation formula is officially adopted by MoSPI for compiling the All-India Consumer Price Index (CPI)?",
                        "options": [
                            "Fisher's Ideal Geometric Mean Index Formula",
                            "Modified Laspeyres Formula with fixed base year expenditure weights",
                            "Paasche Current-Weighted Harmonic Mean Formula",
                            "Carli Unweighted Elementary Arithmetic Mean Index"
                        ],
                        "correct_option_index": 1,
                        "explanation": "MoSPI compiles the All-India CPI using the Modified Laspeyres formula, where base-period expenditure shares from the Household Consumer Expenditure Survey (HCES) serve as fixed weights.",
                        "citation": "CPI Manual, Section 4: Index Compilation Formula",
                        "blooms_level": BloomsLevel.UNDERSTAND.value,
                        "difficulty_level": 2,
                    },
                    {
                        "question_text": "At the elementary aggregate level within a local market, which aggregation method is utilized to combine individual price quotations in CPI?",
                        "options": [
                            "Arithmetic Mean (Dutot Index)",
                            "Geometric Mean (Jevons Index)",
                            "Median Price Selection Method",
                            "Harmonic Mean Index"
                        ],
                        "correct_option_index": 1,
                        "explanation": "In Stage 1 of CPI compilation, elementary aggregate price relatives of individual varieties are compiled using the Geometric Mean (Jevons Index) to avoid substitution bias.",
                        "citation": "CPI Manual, Section 4: Stage 1 Elementary Aggregation",
                        "blooms_level": BloomsLevel.REMEMBER.value,
                        "difficulty_level": 2,
                    },
                    {
                        "question_text": "In the All-India CPI (Combined) weighting diagram (Base 2012=100), which commodity group carries the largest weight of approximately 45.86%?",
                        "options": [
                            "Fuel and Light Group",
                            "Housing Group (Urban)",
                            "Food and Beverages Group",
                            "Miscellaneous Services Group"
                        ],
                        "correct_option_index": 2,
                        "explanation": "Food and Beverages represents the single largest expenditure share in the Indian consumption basket, accounting for 45.86% in the All-India CPI Combined index.",
                        "citation": "CPI Manual, Section 2: Weighting Diagram",
                        "blooms_level": BloomsLevel.APPLY.value,
                        "difficulty_level": 2,
                    },
                    {
                        "question_text": "Why is the Laspeyres base-weighted formula preferred over the Paasche formula for monthly CPI releases in India?",
                        "options": [
                            "Paasche requires current-period quantity weights which cannot be operationally collected on a monthly basis",
                            "Laspeyres formula mathematically eliminates the substitution effect in consumer spending",
                            "The UN Fundamental Principles explicitly ban current-period weighted indices",
                            "Paasche formula results in higher inflation estimates in every economic cycle"
                        ],
                        "correct_option_index": 0,
                        "explanation": "Collecting updated consumption quantity weights every month is impossible across India's population; hence fixed base weights from periodic expenditure surveys (Laspeyres) are necessary.",
                        "citation": "CPI Manual, Section 4.1",
                        "blooms_level": BloomsLevel.ANALYZE.value,
                        "difficulty_level": 3,
                    },
                    {
                        "question_text": "When a price quotation for a seasonal item like seasonal vegetables is temporarily unavailable, which imputation procedure is mandated by MoSPI?",
                        "options": [
                            "Permanent drop of the item from that month's state index calculation",
                            "Cell-mean imputation based on price movements of similar varieties, or variable monthly baskets",
                            "Directly inserting the maximum market price observed during the preceding calendar year",
                            "Setting the price relative to zero for the entire reporting quarter"
                        ],
                        "correct_option_index": 1,
                        "explanation": "MoSPI guidelines prescribe cell-mean imputation (borrowing the trend of similar varieties in the same market) or counter-seasonal variable monthly baskets to prevent artificial spikes.",
                        "citation": "CPI Manual, Section 5: Missing Quotations & Seasonal Items",
                        "blooms_level": BloomsLevel.EVALUATE.value,
                        "difficulty_level": 3,
                    }
                ]
            },
            {
                "title": "Periodic Labour Force Survey (PLFS) Sampling Methodology & Concepts",
                "description": "Official NSS / NSO guidelines on stratified two-stage sampling, PPSWR selection of census villages, UPS vs CWS, and key labour indicators.",
                "filename": "plfs_sampling_and_concepts.txt",
                "file_type": "txt",
                "file_path": "sample_data/plfs_sampling_and_concepts.txt",
                "competency_code": "STAT-SURV",
                "target_level": 3,
                "quiz_title": "Diagnostic Assessment: PLFS Sampling Methodology & Employment Measurement",
                "questions": [
                    {
                        "question_text": "In the sampling design of the Periodic Labour Force Survey (PLFS), how are the First Stage Units (FSUs) selected in rural and urban areas?",
                        "options": [
                            "Simple Random Sampling without Replacement (SRSWOR)",
                            "Probability Proportional to Size (PPS) where size is village/block population",
                            "Voluntary selection based on road accessibility",
                            "Systematic sampling using land area in hectares"
                        ],
                        "correct_option_index": 1,
                        "explanation": "FSUs (Census villages in rural, UFS blocks in urban) are selected with Probability Proportional to Size (PPSWR) or systematic PPS to minimize sampling variance for population totals.",
                        "citation": "PLFS Sampling Methodology, Section 2: Sampling Stages",
                        "blooms_level": BloomsLevel.REMEMBER.value,
                        "difficulty_level": 3,
                    },
                    {
                        "question_text": "Under the Current Weekly Status (CWS) approach, what is the minimum duration of economic activity required during the 7-day reference week for a person to be considered employed?",
                        "options": [
                            "At least 1 hour on at least one day during the 7-day reference week",
                            "At least 4 hours each day for at least 4 consecutive days",
                            "A minimum of 40 aggregate working hours across the full calendar week",
                            "Continuous employment throughout the preceding 30 calendar days"
                        ],
                        "correct_option_index": 0,
                        "explanation": "Under the Current Weekly Status (CWS) framework adopted from ILO standards, a person is classified as employed if they engaged in any economic activity for at least 1 hour on any single day of the 7-day reference period.",
                        "citation": "PLFS Concepts & Definitions, Section 3.2",
                        "blooms_level": BloomsLevel.UNDERSTAND.value,
                        "difficulty_level": 2,
                    }
                ]
            }
        ]

        for mat_info in sample_materials:
            # Read full text
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), mat_info["file_path"])
            text_content = ""
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()

            material = LearningMaterial(
                uploader_id=faculty_user.id,
                title=mat_info["title"],
                description=mat_info["description"],
                filename=mat_info["filename"],
                file_type=mat_info["file_type"],
                file_size_bytes=len(text_content.encode("utf-8")),
                file_path=mat_info["file_path"],
                extracted_text=text_content,
                status="READY",
            )
            db.add(material)
            db.flush()

            # Seed Chunks
            chunk = MaterialChunk(
                material_id=material.id,
                chunk_index=0,
                chunk_text=text_content[:1500],
                page_or_slide_number=1,
                section_title="Official Methodology Guidelines",
            )
            db.add(chunk)

            # Create Quiz
            quiz = Quiz(
                material_id=material.id,
                title=mat_info["quiz_title"],
                description=f"AI-generated adaptive assessment based on {mat_info['title']}",
                competency_code=mat_info["competency_code"],
                target_level=mat_info["target_level"],
                total_questions=len(mat_info["questions"]),
                time_limit_minutes=15,
                pass_percentage=70.0,
                is_adaptive=True,
            )
            db.add(quiz)
            db.flush()

            for q_data in mat_info["questions"]:
                q = Question(
                    quiz_id=quiz.id,
                    question_text=q_data["question_text"],
                    options=q_data["options"],
                    correct_option_index=q_data["correct_option_index"],
                    explanation=q_data["explanation"],
                    citation=q_data["citation"],
                    blooms_level=q_data["blooms_level"],
                    difficulty_level=q_data["difficulty_level"],
                )
                db.add(q)

        print("      -> Successfully ingested official manuals and generated benchmark adaptive quizzes.")

        # 7. Seed MoSPI Digital Skill Passport & QR-Verified Credential for Pooja Sharma
        print("[7/7] Seeding MoSPI Digital Skill Passport Credentials...")
        cred = DigitalCredential(
            user_id=jso_user.id,
            credential_code="MOSPI-CRED-STAT-SURV-L3",
            title="Certified Official Statistics Practitioner: Survey Design & Sampling (NSS)",
            competency_code="STAT-SURV",
            level_awarded=3,
            issued_date=datetime(2026, 8, 15, 10, 0, 0),
            qr_code_hash="c5a4d6f8e2b10938f45a7b8c9d0e1f2a3b4c5d6e",
            verification_url="http://localhost:3000/verify/MOSPI-CRED-STAT-SURV-L3",
            certificate_pdf_url="/reports/cert_pooja_sharma_stat_surv.pdf",
            is_verified=True,
        )
        db.add(cred)

        # Seed sample chat message in Sankhyiki Mitra
        chat_msg1 = ChatMessage(
            user_id=jso_user.id,
            session_id="default",
            role="user",
            content="What is the difference between GVA at basic prices and GDP at market prices?",
        )
        chat_msg2 = ChatMessage(
            user_id=jso_user.id,
            session_id="default",
            role="assistant",
            content="In accordance with the SNA 2008 framework adopted by MoSPI, headline growth is measured by **GDP at market prices**, whereas sectoral output is tracked via **GVA at basic prices**.\n\n**Fundamental Equation:**\n$$\\text{GDP at Market Prices} = \\text{GVA at Basic Prices} + \\text{Product Taxes} - \\text{Product Subsidies}$$\n\n• **Product Taxes**: Levied per unit of output (e.g. GST, customs, central excise).\n• **Production Taxes**: Paid on the production activity itself regardless of output volume (e.g. stamp duty, land revenue).",
            sources=[{"title": "National Accounts Statistics Sources & Methods", "citation": "CSO National Accounts Manual, Section 2.1", "snippet": "GVA at basic prices excludes product taxes and includes product subsidies."}]
        )
        db.add_all([chat_msg1, chat_msg2])

        db.commit()
        print("=" * 60)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Demo Personas Ready:")
        print("1. JSO Pooja Sharma    (Learner)    : jso.sharma@mospi.gov.in    / Password@123")
        print("2. AD Rajesh Verma     (Supervisor) : ad.verma@mospi.gov.in     / Password@123")
        print("3. Dr. Sunita Rao      (Trainer)    : faculty.nssta@nic.in      / Password@123")
        print("4. Alok Mathur         (Admin)      : admin.cadre@mospi.gov.in  / Password@123")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
