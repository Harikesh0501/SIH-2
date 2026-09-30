import io
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import qrcode
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.competency import Competency, CompetencyLevel, UserCompetency, RoleBenchmark
from app.models.course import Course, Enrollment, EnrollmentStatus
from app.models.assessment import QuizAttempt, Quiz
from app.models.passport import DigitalCredential

# Standard Level Labels in MoSPI Competency Framework
LEVEL_LABELS = {
    1: "Basic (Foundation)",
    2: "Intermediate (Working Knowledge)",
    3: "Proficient (Applied Practice)",
    4: "Advanced (Analytical & Advisory)",
    5: "Expert (Policy & Research Lead)"
}

CADRE_NAMES = {
    "ISS": "Indian Statistical Service (Group 'A' Central Service)",
    "SSS": "Subordinate Statistical Service (Group 'B' Gazetted / Non-Gazetted)",
    "CONTRACTUAL": "Contractual / Specialist Statistical Consultant",
    "OTHER": "Departmental / Allied Cadre"
}

DIVISION_NAMES = {
    "FOD": "Field Operations Division (NSS Survey Operations)",
    "NAD": "National Accounts Division (GDP, GVA & Macro Aggregates)",
    "ESD": "Economic Statistics Division (CPI, IIP & ASI Indices)",
    "SDRD": "Survey Design and Research Division (Methodology & Schedules)",
    "DPD": "Data Processing Division (Tabulation & Software)",
    "SSD": "Social Statistics Division (Millennium/Sustainable Goals, Gender)",
    "DIID": "Data Informatics & Innovation Division (Big Data & Open Data)",
    "NSSTA": "National Statistical Systems Training Academy"
}

_QR_CACHE: Dict[str, str] = {}

class PassportService:
    @staticmethod
    def generate_qr_code_base64(data: str, box_size: int = 5, border: int = 2) -> str:
        """
        Generates a crisp monochrome (Black & White) QR Code as a base64-encoded PNG Data URI with in-memory caching.
        """
        if data in _QR_CACHE:
            return _QR_CACHE[data]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        result = f"data:image/png;base64,{b64_str}"
        _QR_CACHE[data] = result
        return result

    @staticmethod
    def generate_sha256_hash(payload_str: str) -> str:
        """
        Generates SHA-256 cryptographic signature for verifiable credentials.
        """
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    @classmethod
    def get_karmayogi_id(cls, user: User) -> str:
        cadre_code = user.cadre or "SSS"
        return f"KY-MOSPI-{cadre_code}-{user.id:04d}"

    @classmethod
    def sync_user_credentials(cls, db: Session, user: User) -> List[DigitalCredential]:
        """
        Synchronizes verified accomplishments into official DigitalCredential rows.
        Creates credentials for any competency where level >= 2 or verified via SUPERVISOR/QUIZ/IGOT.
        """
        existing_creds = db.query(DigitalCredential).filter(DigitalCredential.user_id == user.id).all()
        if existing_creds:
            return existing_creds
        existing_by_code = {c.competency_code: c for c in existing_creds}

        user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()
        comp_map = {c.id: c for c in db.query(Competency).all()}

        updated_or_created = False
        for uc in user_comps:
            comp = comp_map.get(uc.competency_id)
            if not comp:
                continue

            # Eligible if level >= 2 or assessed via supervisor/quiz
            if uc.current_level >= 2 or uc.assessed_via in ["SUPERVISOR", "QUIZ", "IGOT"]:
                cred = existing_by_code.get(comp.code)
                if cred:
                    # Update level if promoted
                    if uc.current_level > cred.level_awarded:
                        cred.level_awarded = uc.current_level
                        cred.title = f"Certified Official Statistics Practitioner: {comp.name} (Level {uc.current_level})"
                        hash_payload = f"MOSPI:{user.id}:{comp.code}:{uc.current_level}:{datetime.utcnow().isoformat()}:SALT_2026"
                        cred.qr_code_hash = cls.generate_sha256_hash(hash_payload)
                        updated_or_created = True
                else:
                    # Create new credential
                    unique_code = f"MOSPI-CRED-{comp.code}-L{uc.current_level}-{user.id:04d}"
                    hash_payload = f"MOSPI:{user.id}:{comp.code}:{uc.current_level}:{datetime.utcnow().isoformat()}:SALT_2026"
                    sha_hash = cls.generate_sha256_hash(hash_payload)
                    verification_url = f"http://localhost:3000/verify/{unique_code}"
                    
                    new_cred = DigitalCredential(
                        user_id=user.id,
                        credential_code=unique_code,
                        title=f"Certified Official Statistics Practitioner: {comp.name}",
                        competency_code=comp.code,
                        level_awarded=uc.current_level,
                        issued_date=datetime.utcnow(),
                        qr_code_hash=sha_hash,
                        certificate_pdf_url=f"/api/reports/officer-skill-card/{user.id}",
                        verification_url=verification_url,
                        is_verified=True,
                    )
                    db.add(new_cred)
                    updated_or_created = True

        if updated_or_created:
            db.commit()

        return db.query(DigitalCredential).filter(DigitalCredential.user_id == user.id).order_by(DigitalCredential.issued_date.desc()).all()

    @classmethod
    def evaluate_mastery_badges(cls, db: Session, user: User, user_comps: List[UserCompetency]) -> List[Dict[str, Any]]:
        """
        Dynamically computes earned domain badges and honours based on MoSPI criteria.
        """
        badges = []
        comp_level_map = {uc.competency.code: uc.current_level for uc in user_comps if uc.competency}

        # 1. Survey Specialist (NSS)
        if comp_level_map.get("STAT-SURV", 0) >= 3:
            badges.append({
                "id": "BADGE-SURV-NSS",
                "code": "STAT-SURV-SPEC",
                "title": "National Survey Specialist (NSS)",
                "category": "STATISTICAL",
                "tier": "GOLD",
                "description": "Demonstrated Level 3+ mastery in multi-stage stratified sampling, NSS frame design, and field validation.",
                "criteria": "Level 3+ in Survey Design & Sampling Methods (NSS)",
                "earned_date": "2026-08-15T10:00:00",
                "icon": "shield-check"
            })

        # 2. National Accounts Architect (SNA 2008)
        if comp_level_map.get("STAT-NAS", 0) >= 3:
            badges.append({
                "id": "BADGE-NAS-ARCH",
                "code": "STAT-NAS-SPEC",
                "title": "National Accounts Architect (SNA 2008)",
                "category": "STATISTICAL",
                "tier": "GOLD",
                "description": "Recognized for expertise in Gross Value Added (GVA), GDP compiling, and National Accounts conceptual frameworks.",
                "criteria": "Level 3+ in National Accounts & GVA/GDP (SNA 2008)",
                "earned_date": "2026-08-20T10:00:00",
                "icon": "activity"
            })

        # 3. Price Index & Inflation Practitioner
        if comp_level_map.get("STAT-PRICE", 0) >= 2:
            badges.append({
                "id": "BADGE-PRICE-CPI",
                "code": "STAT-PRICE-SPEC",
                "title": "Price Index & Inflation Practitioner",
                "category": "STATISTICAL",
                "tier": "SILVER",
                "description": "Proficient in CPI basket formulation, elementary price aggregation (Jevons formula), and inflation indicators.",
                "criteria": "Level 2+ in Price Statistics, CPI & Inflation Indices",
                "earned_date": "2026-08-10T10:00:00",
                "icon": "trending-up"
            })

        # 4. Data Quality & Statistical Ethics Guardian
        if comp_level_map.get("STAT-DQAF", 0) >= 2 or comp_level_map.get("MGMT-ETHC", 0) >= 2:
            badges.append({
                "id": "BADGE-ETHICS-DQAF",
                "code": "STAT-DQAF-SPEC",
                "title": "Data Quality & Statistical Ethics Guardian",
                "category": "DIGITAL_GOVERNANCE",
                "tier": "SILVER",
                "description": "Certified in UN Fundamental Principles of Official Statistics and MoSPI DQAF audit guidelines.",
                "criteria": "Level 2+ in Data Quality (DQAF) or Statistical Ethics",
                "earned_date": "2026-07-25T10:00:00",
                "icon": "award"
            })

        # 5. Modern Statistical Computing (Python / R)
        if comp_level_map.get("TECH-PYST", 0) >= 2 or comp_level_map.get("TECH-RSTA", 0) >= 2:
            badges.append({
                "id": "BADGE-TECH-DATA",
                "code": "TECH-DATA-SPEC",
                "title": "Statistical Computing & Python Specialist",
                "category": "TECHNICAL",
                "tier": "BRONZE",
                "description": "Proficient in algorithmic survey data wrangling, reproducible workflows, and statistical computation.",
                "criteria": "Level 2+ in Python for Official Statistics or R",
                "earned_date": "2026-07-15T10:00:00",
                "icon": "terminal"
            })

        # 6. Adaptive Assessment Honors (CAT)
        passed_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user.id,
            QuizAttempt.score >= 75.0
        ).count()
        if passed_attempts > 0:
            badges.append({
                "id": "BADGE-CAT-HONORS",
                "code": "CAT-HONORS",
                "title": "Adaptive Assessment Honors",
                "category": "ASSESSMENT",
                "tier": "HONORS",
                "description": "Demonstrated top-tier performance on NSSTA Computerized Adaptive Testing with automatic competency promotion.",
                "criteria": "Score 75%+ on Adaptive Multimodal CAT Assessment",
                "earned_date": "2026-09-28T10:00:00",
                "icon": "zap"
            })

        # 7. iGOT Karmayogi Continuous Learner
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.status == EnrollmentStatus.COMPLETED.value
        ).count()
        if completed_enrollments > 0:
            badges.append({
                "id": "BADGE-IGOT-LEARNER",
                "code": "IGOT-LEARNER",
                "title": "iGOT Karmayogi Continuous Learner",
                "category": "LEARNING",
                "tier": "COMMENDATION",
                "description": "Actively upskilling through Mission Karmayogi digital civil service pathways.",
                "criteria": "Completed 1+ iGOT Karmayogi learning pathways",
                "earned_date": "2026-09-01T10:00:00",
                "icon": "book-open"
            })

        return badges

    @classmethod
    def get_officer_passport(cls, db: Session, user: User) -> Dict[str, Any]:
        """
        Compiles the full MoSPI Digital Skill Passport for an officer.
        """
        # Ensure credentials are in sync
        credentials_records = cls.sync_user_credentials(db, user)

        karmayogi_id = cls.get_karmayogi_id(user)
        master_verification_url = f"http://localhost:3000/verify/passport/{karmayogi_id}"
        master_qr_code = cls.generate_qr_code_base64(master_verification_url, box_size=6)

        # Retrieve user competencies
        user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()
        benchmarks = db.query(RoleBenchmark).filter(RoleBenchmark.designation == user.designation).all()
        benchmark_map = {b.competency_id: b.required_level for b in benchmarks}

        all_competencies = db.query(Competency).all()
        all_levels = db.query(CompetencyLevel).all()
        level_descriptor_map = {(cl.competency_id, cl.level): cl.descriptor for cl in all_levels}

        user_comp_map = {uc.competency_id: uc for uc in user_comps}

        # Build Domain breakdown
        domain_groups: Dict[str, List[Dict[str, Any]]] = {
            "STATISTICAL": [],
            "TECHNICAL": [],
            "DIGITAL_GOVERNANCE": [],
            "BEHAVIOURAL_MANAGERIAL": []
        }

        total_current_levels = 0
        total_benchmark_levels = 0
        verified_count = 0

        for comp in all_competencies:
            uc = user_comp_map.get(comp.id)
            current_level = uc.current_level if uc else 0
            assessed_via = uc.assessed_via if uc else "NOT_ASSESSED"
            confidence = uc.confidence_score if uc else 0.0
            last_eval = uc.last_evaluated_at.isoformat() if uc and uc.last_evaluated_at else None
            req_level = benchmark_map.get(comp.id, 2)

            if current_level > 0:
                total_current_levels += current_level
            total_benchmark_levels += req_level

            if assessed_via in ["SUPERVISOR", "QUIZ", "IGOT"] and current_level >= 2:
                verified_count += 1

            descriptor = level_descriptor_map.get((comp.id, current_level), "Foundational familiarity") if current_level > 0 else "Not yet assessed"

            comp_info = {
                "competency_id": comp.id,
                "code": comp.code,
                "name": comp.name,
                "domain": comp.domain,
                "current_level": current_level,
                "target_level": req_level,
                "level_label": LEVEL_LABELS.get(current_level, "Not Assessed"),
                "descriptor": descriptor,
                "assessed_via": assessed_via,
                "is_verified": assessed_via in ["SUPERVISOR", "QUIZ", "IGOT"],
                "confidence_score": confidence,
                "last_evaluated_at": last_eval,
            }

            if comp.domain in domain_groups:
                domain_groups[comp.domain].append(comp_info)
            else:
                domain_groups.setdefault(comp.domain, []).append(comp_info)

        # Proficiency index
        proficiency_pct = round((total_current_levels / max(total_benchmark_levels, 1)) * 100, 1)
        proficiency_pct = min(proficiency_pct, 100.0)

        # Format Verified Credentials
        comp_by_code = {c.code: c for c in all_competencies}
        credentials_list = []
        for cred in credentials_records:
            comp = comp_by_code.get(cred.competency_code)
            cred_url = cred.verification_url or f"http://localhost:3000/verify/{cred.credential_code}"

            credentials_list.append({
                "id": cred.id,
                "credential_code": cred.credential_code,
                "title": cred.title,
                "competency_code": cred.competency_code,
                "competency_name": comp.name if comp else cred.competency_code,
                "domain": comp.domain if comp else "STATISTICAL",
                "level_awarded": cred.level_awarded,
                "level_label": LEVEL_LABELS.get(cred.level_awarded, f"Level {cred.level_awarded}"),
                "issued_date": cred.issued_date.isoformat() if cred.issued_date else None,
                "qr_code_hash": cred.qr_code_hash,
                "qr_code_image": master_qr_code,
                "verification_url": cred_url,
                "certificate_pdf_url": cred.certificate_pdf_url or f"/api/reports/officer-skill-card/{user.id}",
                "is_verified": cred.is_verified,
                "issuer": "National Statistical Systems Training Academy (NSSTA), MoSPI, Govt. of India"
            })

        # Badges
        badges = cls.evaluate_mastery_badges(db, user, user_comps)

        # Completed Courses (Dual-track transcript)
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.status == EnrollmentStatus.COMPLETED.value
        ).all()
        
        courses_transcript = []
        training_hours = 0.0
        for en in completed_enrollments:
            course = en.course
            if course:
                training_hours += (course.duration_hours or 0.0)
                courses_transcript.append({
                    "enrollment_id": en.id,
                    "course_id": course.id,
                    "external_id": course.external_id,
                    "title": course.title,
                    "source": course.source, # IGOT_KARMAYOGI or NSSTA_TPAC
                    "delivery_mode": course.delivery_mode,
                    "provider": course.provider,
                    "duration_hours": course.duration_hours,
                    "completed_at": en.completed_at.isoformat() if en.completed_at else en.enrolled_at.isoformat(),
                    "certificate_id": en.certificate_id or f"CERT-KY-{course.external_id}-{user.id}"
                })

        # Recent Assessments
        recent_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user.id
        ).order_by(QuizAttempt.created_at.desc()).limit(5).all()

        assessments_list = []
        for att in recent_attempts:
            quiz = att.quiz
            assessments_list.append({
                "attempt_id": att.id,
                "quiz_id": att.quiz_id,
                "quiz_title": quiz.title if quiz else "Adaptive Competency Assessment",
                "competency_code": quiz.competency_code if quiz and quiz.competency_code else "STAT-GEN",
                "score": att.score,
                "percentage": att.percentage,
                "passed": att.passed,
                "time_taken_seconds": att.time_taken_seconds,
                "created_at": att.created_at.isoformat() if att.created_at else None
            })

        return {
            "officer": {
                "id": user.id,
                "karmayogi_id": karmayogi_id,
                "full_name": user.full_name,
                "email": user.email,
                "cadre": user.cadre,
                "cadre_full_name": CADRE_NAMES.get(user.cadre, user.cadre),
                "designation": user.designation,
                "division": user.division,
                "division_full_name": DIVISION_NAMES.get(user.division, user.division),
                "organization": user.organization or "Ministry of Statistics & Programme Implementation (MoSPI)",
                "experience_years": user.experience_years,
                "education": user.education,
                "avatar_url": user.avatar_url,
                "passport_status": "VERIFIED_ACTIVE",
                "issued_date": user.created_at.isoformat() if user.created_at else None,
                "last_synced_at": datetime.utcnow().isoformat(),
                "master_qr_code": master_qr_code,
                "verification_url": master_verification_url
            },
            "summary_metrics": {
                "total_competencies_in_framework": len(all_competencies),
                "competencies_assessed": len(user_comps),
                "competencies_verified": verified_count,
                "overall_proficiency_pct": proficiency_pct,
                "credentials_count": len(credentials_list),
                "badges_earned_count": len(badges),
                "training_hours_completed": round(training_hours, 1),
                "quizzes_passed_count": len([a for a in assessments_list if a["passed"]])
            },
            "domains": [
                {
                    "domain_code": "STATISTICAL",
                    "domain_name": "Domain & Statistical Methods (Core MoSPI)",
                    "competencies": domain_groups.get("STATISTICAL", [])
                },
                {
                    "domain_code": "TECHNICAL",
                    "domain_name": "Technical & Statistical Computing (Python/R/Databases)",
                    "competencies": domain_groups.get("TECHNICAL", [])
                },
                {
                    "domain_code": "DIGITAL_GOVERNANCE",
                    "domain_name": "Digital Systems, Data Architecture & Governance",
                    "competencies": domain_groups.get("DIGITAL_GOVERNANCE", [])
                },
                {
                    "domain_code": "BEHAVIOURAL_MANAGERIAL",
                    "domain_name": "Soft Skills, Ethics & Leadership (Mission Karmayogi)",
                    "competencies": domain_groups.get("BEHAVIOURAL_MANAGERIAL", [])
                }
            ],
            "credentials": credentials_list,
            "badges": badges,
            "completed_courses": courses_transcript,
            "recent_assessments": assessments_list
        }

    @classmethod
    def verify_credential(cls, db: Session, credential_code_or_hash: str) -> Dict[str, Any]:
        """
        Public verification endpoint for audit by any third party or department.
        Matches by credential_code or sha256 qr_code_hash.
        """
        cred = db.query(DigitalCredential).filter(
            (DigitalCredential.credential_code == credential_code_or_hash) |
            (DigitalCredential.qr_code_hash == credential_code_or_hash)
        ).first()

        if not cred:
            return {
                "valid": False,
                "status": "INVALID_OR_NOT_FOUND",
                "message": f"No official MoSPI credential found matching identifier '{credential_code_or_hash}'."
            }

        user = cred.user
        comp = db.query(Competency).filter(Competency.code == cred.competency_code).first()
        level_rec = None
        if comp:
            level_rec = db.query(CompetencyLevel).filter(
                CompetencyLevel.competency_id == comp.id,
                CompetencyLevel.level == cred.level_awarded
            ).first()

        descriptor = level_rec.descriptor if level_rec else "Certified Applied Official Statistics Practitioner"

        # Mask email for privacy (e.g., j***a@mospi.gov.in)
        parts = user.email.split("@")
        masked_email = f"{parts[0][0]}***{parts[0][-1]}@{parts[1]}" if len(parts[0]) > 2 else f"***@{parts[1]}"

        verification_url = cred.verification_url or f"http://localhost:3000/verify/{cred.credential_code}"
        qr_img = cls.generate_qr_code_base64(verification_url, box_size=5)

        return {
            "valid": True,
            "status": "OFFICIALLY_VERIFIED",
            "audit_trail": {
                "issuer": "National Statistical Systems Training Academy (NSSTA), Ministry of Statistics & Programme Implementation (MoSPI), Government of India",
                "accreditation": "iGOT Karmayogi Civil Services Competency Framework / National Training Policy",
                "verification_timestamp": datetime.utcnow().isoformat(),
                "cryptographic_algorithm": "SHA-256 (Tamper-evident)",
                "hash_signature": cred.qr_code_hash,
                "trust_status": "SECURE_GOV_SEAL_VALID"
            },
            "credential": {
                "credential_code": cred.credential_code,
                "title": cred.title,
                "competency_code": cred.competency_code,
                "competency_name": comp.name if comp else cred.competency_code,
                "domain": comp.domain if comp else "STATISTICAL",
                "level_awarded": cred.level_awarded,
                "level_label": LEVEL_LABELS.get(cred.level_awarded, f"Level {cred.level_awarded}"),
                "level_descriptor": descriptor,
                "issued_date": cred.issued_date.isoformat() if cred.issued_date else None,
                "is_verified": cred.is_verified
            },
            "recipient": {
                "officer_id": user.id,
                "karmayogi_id": cls.get_karmayogi_id(user),
                "full_name": user.full_name,
                "masked_email": masked_email,
                "cadre": user.cadre,
                "cadre_full_name": CADRE_NAMES.get(user.cadre, user.cadre),
                "designation": user.designation,
                "division": user.division,
                "division_full_name": DIVISION_NAMES.get(user.division, user.division),
                "organization": user.organization or "Ministry of Statistics & Programme Implementation (MoSPI)"
            },
            "qr_code_image": qr_img
        }

    @classmethod
    def verify_officer_passport(cls, db: Session, identifier: str) -> Dict[str, Any]:
        """
        Public verification of an officer's entire skill passport by karmayogi_id or officer_id.
        """
        user = None
        # Try finding by user.id if digit
        if identifier.isdigit():
            user = db.query(User).filter(User.id == int(identifier)).first()
        
        # If not, try matching karmayogi_id format KY-MOSPI-{cadre}-{id}
        if not user and "KY-MOSPI-" in identifier:
            parts = identifier.split("-")
            if len(parts) >= 4 and parts[-1].isdigit():
                user_id = int(parts[-1])
                user = db.query(User).filter(User.id == user_id).first()

        # Fallback search by email or name
        if not user:
            user = db.query(User).filter((User.email == identifier) | (User.full_name == identifier)).first()

        if not user:
            return {
                "valid": False,
                "status": "PASSPORT_NOT_FOUND",
                "message": f"No officer found for Karmayogi identifier '{identifier}'."
            }

        passport = cls.get_officer_passport(db, user)
        return {
            "valid": True,
            "status": "OFFICIALLY_VERIFIED",
            "verification_type": "OFFICER_FULL_PASSPORT",
            "audit_trail": {
                "issuer": "Ministry of Statistics & Programme Implementation (MoSPI) / NSSTA",
                "verification_timestamp": datetime.utcnow().isoformat(),
                "trust_status": "ACTIVE_AUTHENTIC_GOV_RECORD"
            },
            "officer": passport["officer"],
            "summary_metrics": passport["summary_metrics"],
            "badges_count": len(passport["badges"]),
            "credentials_count": len(passport["credentials"]),
            "top_credentials": passport["credentials"][:3],
            "badges": passport["badges"]
        }
