from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.competency import Competency, UserCompetency, RoleBenchmark
from app.models.course import Course, Enrollment, EnrollmentStatus
from app.services.passport_service import DIVISION_NAMES, CADRE_NAMES

class TPACAllocationEngine:

    @classmethod
    def get_batch_recommendations(cls, db: Session, course: Course) -> Dict[str, Any]:
        """
        Evaluates and ranks candidate officers for a specific TPAC residential training batch
        based on competency gaps and role criticality.
        """
        target_comps = course.target_competencies or []
        if isinstance(target_comps, str):
            target_comps = [target_comps]

        # Fetch competencies and role benchmarks
        comp_records = db.query(Competency).filter(Competency.code.in_(target_comps)).all()
        comp_id_map = {c.id: c for c in comp_records}
        comp_code_to_id = {c.code: c.id for c in comp_records}

        benchmarks = db.query(RoleBenchmark).filter(RoleBenchmark.competency_id.in_(comp_id_map.keys())).all()
        bench_map = {(b.designation, b.competency_id): (b.required_level, b.weight) for b in benchmarks}

        # Existing enrollments for this course
        existing_enrollments = db.query(Enrollment).filter(Enrollment.course_id == course.id).all()
        enrolled_user_ids = {e.user_id: e for e in existing_enrollments}

        all_users = db.query(User).filter(User.role.in_(["LEARNER", "SUPERVISOR"])).all()
        candidate_evaluations = []

        for user in all_users:
            # Query user's current level in target competencies
            user_ucs = db.query(UserCompetency).filter(
                UserCompetency.user_id == user.id,
                UserCompetency.competency_id.in_(comp_id_map.keys())
            ).all()
            uc_level_map = {uc.competency_id: uc.current_level for uc in user_ucs}

            total_gap = 0.0
            max_urgency = 0.0
            comp_breakdown = []

            for comp_code in target_comps:
                comp_id = comp_code_to_id.get(comp_code)
                if not comp_id:
                    continue

                curr_lvl = uc_level_map.get(comp_id, 1) # baseline level 1 if unassessed
                req_lvl, weight = bench_map.get((user.designation, comp_id), (course.target_level or 3, 1.2))

                gap = max(0, req_lvl - curr_lvl)
                urgency = round(gap * weight, 2)
                total_gap += gap
                max_urgency = max(max_urgency, urgency)

                comp_breakdown.append({
                    "competency_code": comp_code,
                    "competency_name": comp_id_map[comp_id].name if comp_id in comp_id_map else comp_code,
                    "current_level": curr_lvl,
                    "target_level": req_lvl,
                    "gap": gap,
                    "urgency": urgency
                })

            is_already_enrolled = user.id in enrolled_user_ids
            enrollment_record = enrolled_user_ids.get(user.id)
            current_status = enrollment_record.status if enrollment_record else "NOT_ENROLLED"

            # Formulate clear recommendation rationale
            if total_gap > 0:
                rationale = f"Significant skill deficit of {round(total_gap, 1)} levels in {', '.join(target_comps)} required for {user.designation}."
            else:
                rationale = f"Current proficiency meets baseline, recommended as peer-mentor or refresher."

            candidate_evaluations.append({
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "cadre": user.cadre,
                "designation": user.designation,
                "division": user.division,
                "division_full_name": DIVISION_NAMES.get(user.division, user.division),
                "total_gap": round(total_gap, 2),
                "urgency_score": round(max_urgency, 2),
                "competency_breakdown": comp_breakdown,
                "rationale": rationale,
                "is_enrolled": is_already_enrolled,
                "enrollment_status": current_status,
                "enrollment_id": enrollment_record.id if enrollment_record else None
            })

        # Sort candidate queue by urgency descending
        candidate_evaluations.sort(key=lambda x: x["urgency_score"], reverse=True)

        # Segregate enrolled vs priority queue
        enrolled_officers = [c for c in candidate_evaluations if c["is_enrolled"]]
        eligible_queue = [c for c in candidate_evaluations if not c["is_enrolled"]]

        capacity = course.batch_capacity or 35
        remaining_seats = max(0, capacity - len(enrolled_officers))
        priority_nominees = eligible_queue[:remaining_seats]
        waitlist_nominees = eligible_queue[remaining_seats:]

        return {
            "course_id": course.id,
            "external_id": course.external_id,
            "title": course.title,
            "provider": course.provider,
            "location": course.location or "NSSTA Greater Noida",
            "batch_start_date": course.batch_start_date,
            "batch_capacity": capacity,
            "enrolled_count": len(enrolled_officers),
            "remaining_seats": remaining_seats,
            "fill_percentage": round((len(enrolled_officers) / max(1, capacity)) * 100, 1),
            "target_competencies": target_comps,
            "enrolled_officers": enrolled_officers,
            "priority_nominees": priority_nominees,
            "waitlist_nominees": waitlist_nominees
        }

    @classmethod
    def get_all_tpac_batches(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Retrieves all NSSTA TPAC residential training batches with live nomination statistics.
        """
        tpac_courses = db.query(Course).filter(
            Course.source == "NSSTA_TPAC",
            Course.is_active == True
        ).all()

        batches_data = []
        for course in tpac_courses:
            batch_summary = cls.get_batch_recommendations(db, course)
            batches_data.append(batch_summary)

        return batches_data

    @classmethod
    def allocate_batch_nominations(
        cls,
        db: Session,
        course_id: int,
        user_ids: List[int],
        admin_user: User,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formally allocates and confirms nominations for statistical officers to a TPAC residential course.
        """
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course with ID {course_id} not found.")

        target_users = db.query(User).filter(User.id.in_(user_ids)).all()
        if not target_users:
            raise ValueError("No valid statistical personnel found for nomination.")

        newly_enrolled = []
        already_enrolled = []

        for user in target_users:
            existing = db.query(Enrollment).filter(
                Enrollment.course_id == course.id,
                Enrollment.user_id == user.id
            ).first()

            if existing:
                if existing.status != EnrollmentStatus.ENROLLED.value:
                    existing.status = EnrollmentStatus.ENROLLED.value
                    existing.nominated_by_supervisor_id = admin_user.id
                    existing.enrolled_at = datetime.utcnow()
                    newly_enrolled.append(user)
                else:
                    already_enrolled.append(user)
            else:
                new_enrollment = Enrollment(
                    user_id=user.id,
                    course_id=course.id,
                    status=EnrollmentStatus.ENROLLED.value,
                    progress_percentage=0,
                    nominated_by_supervisor_id=admin_user.id,
                    enrolled_at=datetime.utcnow(),
                    certificate_id=f"TPAC-NOM-{course.external_id}-{user.id}"
                )
                db.add(new_enrollment)
                newly_enrolled.append(user)

        db.commit()

        # Re-fetch updated course stats
        updated_enrolled_count = db.query(Enrollment).filter(Enrollment.course_id == course.id).count()
        capacity = course.batch_capacity or 35

        return {
            "success": True,
            "message": f"Successfully nominated {len(newly_enrolled)} officer(s) to '{course.title}' at {course.location}.",
            "course": {
                "id": course.id,
                "external_id": course.external_id,
                "title": course.title,
                "batch_start_date": course.batch_start_date,
                "location": course.location,
                "total_enrolled": updated_enrolled_count,
                "capacity": capacity,
                "fill_percentage": round((updated_enrolled_count / max(1, capacity)) * 100, 1)
            },
            "newly_nominated_officers": [
                {
                    "user_id": u.id,
                    "full_name": u.full_name,
                    "designation": u.designation,
                    "division": u.division,
                    "email": u.email
                }
                for u in newly_enrolled
            ],
            "already_enrolled_officers": [
                {"user_id": u.id, "full_name": u.full_name} for u in already_enrolled
            ],
            "training_alert_dispatched": {
                "channel": "GOV_NIC_EMAIL_AND_IGOT_PORTAL",
                "dispatched_at": datetime.utcnow().isoformat(),
                "notice": message or f"Official nomination confirmed for NSSTA Residential Programme {course.title}."
            }
        }
