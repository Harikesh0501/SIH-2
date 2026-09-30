from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.course import Course, CourseSource, Enrollment, EnrollmentStatus
from app.models.competency import Competency, UserCompetency
from app.schemas.recommendation import (
    PathwayResponse,
    RecommendedCourseItem,
    EnrollCourseResponse,
    CompleteWebhookRequest,
    CompleteWebhookResponse,
    NominateBatchRequest,
    NominateBatchResponse,
    NominatedSubordinateResult,
    MyCoursesResponse,
    EnrollmentItem,
)
from app.services.recommender import HybridRecommender
from app.services.igot_client import IGotKarmayogiClient
from app.services.gap_analyzer import CompetencyGapAnalyzer
from app.api.deps import get_current_user, require_supervisor

router = APIRouter(tags=["Recommendations & iGOT Integration"])

# 1. GET /api/recommendations/my-pathway
@router.get("/recommendations/my-pathway", response_model=PathwayResponse)
def get_my_pathway(
    source: Optional[str] = Query(None, description="Filter by course source: IGOT_KARMAYOGI or NSSTA_TPAC"),
    domain: Optional[str] = Query(None, description="Filter by competency domain e.g. Statistical, Technical"),
    max_duration: Optional[float] = Query(None, description="Maximum course duration in hours"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delivers personalized dual-track learning pathways for the authenticated officer.
    Segregates courses into Track A (iGOT Karmayogi) and Track B (NSSTA TPAC).
    """
    return HybridRecommender.get_personalized_pathway(
        db=db,
        user=current_user,
        source_filter=source,
        domain_filter=domain,
        max_duration=max_duration,
    )

# 2. POST /api/igot/enroll/{course_id}
@router.post("/igot/enroll/{course_id}", response_model=EnrollCourseResponse)
@router.post("/recommendations/enroll/{course_id}", response_model=EnrollCourseResponse)
def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dispatches course registration to iGOT Karmayogi API or enrolls in NSSTA TPAC programme.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.is_active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} was not found or is currently inactive."
        )

    # Check existing enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course.id,
    ).first()

    deep_link = None
    if course.source == CourseSource.IGOT_KARMAYOGI.value:
        igot_res = IGotKarmayogiClient.dispatch_enrollment(
            user_email=current_user.email,
            user_cadre=current_user.cadre,
            course_external_id=course.external_id,
        )
        deep_link = igot_res["result"]["deepLink"]

    if enrollment:
        if enrollment.status == EnrollmentStatus.COMPLETED.value:
            return EnrollCourseResponse(
                success=True,
                message=f"You have already successfully completed '{course.title}'.",
                enrollment_id=enrollment.id,
                course_id=course.id,
                course_title=course.title,
                source=course.source,
                status=enrollment.status,
                enrolled_at=enrollment.enrolled_at,
                igot_deep_link=deep_link,
            )
        # Update existing to active enrollment
        enrollment.status = EnrollmentStatus.ENROLLED.value
        enrollment.enrolled_at = datetime.utcnow()
    else:
        enrollment = Enrollment(
            user_id=current_user.id,
            course_id=course.id,
            status=EnrollmentStatus.ENROLLED.value,
            progress_percentage=0,
            enrolled_at=datetime.utcnow(),
        )
        db.add(enrollment)

    db.commit()
    db.refresh(enrollment)

    return EnrollCourseResponse(
        success=True,
        message=f"Successfully registered for '{course.title}' on {course.source}.",
        enrollment_id=enrollment.id,
        course_id=course.id,
        course_title=course.title,
        source=course.source,
        status=enrollment.status,
        enrolled_at=enrollment.enrolled_at,
        igot_deep_link=deep_link,
    )

# 3. POST /api/igot/complete-webhook
@router.post("/igot/complete-webhook", response_model=CompleteWebhookResponse)
def igot_completion_webhook(
    payload: CompleteWebhookRequest,
    db: Session = Depends(get_db),
):
    """
    Receives automated completion triggers from iGOT Karmayogi Bharat or NSSTA Exam Cell.
    Automatically marks course completed and auto-upgrades corresponding competency levels.
    """
    user = db.query(User).filter(User.email == payload.user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{payload.user_email}' not found."
        )

    course = db.query(Course).filter(Course.external_id == payload.course_external_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with external ID '{payload.course_external_id}' not found."
        )

    # Upsert enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.course_id == course.id,
    ).first()

    cert_id = payload.certificate_id or f"CERT-IGOT-{uuid.uuid4().hex[:8].upper()}"
    completion_time = datetime.utcnow()

    if enrollment:
        enrollment.status = EnrollmentStatus.COMPLETED.value
        enrollment.progress_percentage = 100
        enrollment.certificate_id = cert_id
        enrollment.completed_at = completion_time
    else:
        enrollment = Enrollment(
            user_id=user.id,
            course_id=course.id,
            status=EnrollmentStatus.COMPLETED.value,
            progress_percentage=100,
            certificate_id=cert_id,
            enrolled_at=completion_time,
            completed_at=completion_time,
        )
        db.add(enrollment)

    # Auto-Upgrade Competency Scores if passing criteria met (>= 70%)
    upgraded_comps = []
    if payload.score_percentage >= 70.0:
        target_codes = course.target_competencies or []
        for code in target_codes:
            comp = db.query(Competency).filter(Competency.code == code).first()
            if not comp:
                continue

            uc = db.query(UserCompetency).filter(
                UserCompetency.user_id == user.id,
                UserCompetency.competency_id == comp.id,
            ).first()

            old_level = uc.current_level if uc else 1
            new_level = max(old_level, course.target_level)

            if uc:
                uc.current_level = new_level
                uc.assessed_via = "IGOT" if course.source == CourseSource.IGOT_KARMAYOGI.value else "NSSTA_TPAC"
                uc.confidence_score = 0.92
                uc.last_evaluated_at = completion_time
            else:
                uc = UserCompetency(
                    user_id=user.id,
                    competency_id=comp.id,
                    current_level=new_level,
                    assessed_via="IGOT" if course.source == CourseSource.IGOT_KARMAYOGI.value else "NSSTA_TPAC",
                    confidence_score=0.92,
                    last_evaluated_at=completion_time,
                )
                db.add(uc)

            upgraded_comps.append({
                "competency_code": comp.code,
                "competency_name": comp.name,
                "previous_level": old_level,
                "upgraded_level": new_level,
                "assessed_via": uc.assessed_via,
            })

    db.commit()

    # Recalculate new readiness
    new_gap_analysis = CompetencyGapAnalyzer.analyze_gaps(db, user)

    return CompleteWebhookResponse(
        success=True,
        message=f"Course '{course.title}' completion processed for {user.full_name}. Scored {payload.score_percentage}%.",
        user_id=user.id,
        user_name=user.full_name,
        course_title=course.title,
        status="COMPLETED",
        upgraded_competencies=upgraded_comps,
        new_readiness_percentage=new_gap_analysis.overall_readiness_percentage,
    )

# 4. GET /api/enrollments/my-courses
@router.get("/enrollments/my-courses", response_model=MyCoursesResponse)
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the authenticated officer's course enrollments across active, in-progress, and completed states.
    """
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).order_by(Enrollment.enrolled_at.desc()).all()

    items: List[EnrollmentItem] = []
    in_progress_count = 0
    completed_count = 0

    for enr in enrollments:
        c = enr.course
        if not c:
            continue

        if enr.status == EnrollmentStatus.COMPLETED.value:
            completed_count += 1
        elif enr.status in [EnrollmentStatus.ENROLLED.value, EnrollmentStatus.IN_PROGRESS.value]:
            in_progress_count += 1

        nom_name = enr.nominated_by.full_name if enr.nominated_by else None

        items.append(EnrollmentItem(
            enrollment_id=enr.id,
            course_id=c.id,
            external_id=c.external_id,
            source=c.source,
            title=c.title,
            description=c.description,
            provider=c.provider,
            duration_hours=c.duration_hours,
            delivery_mode=c.delivery_mode,
            location=c.location,
            target_competencies=c.target_competencies or [],
            target_level=c.target_level,
            status=enr.status,
            progress_percentage=enr.progress_percentage,
            certificate_id=enr.certificate_id,
            enrolled_at=enr.enrolled_at,
            completed_at=enr.completed_at,
            nominated_by_name=nom_name,
            course_url=c.course_url,
        ))

    return MyCoursesResponse(
        total_enrolled=len(items),
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        courses=items,
    )

# 5. POST /api/recommendations/nominate-batch
@router.post("/recommendations/nominate-batch", response_model=NominateBatchResponse)
def nominate_batch(
    req: NominateBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """
    Enables Division Directors and Supervisors to nominate subordinate statistical officers
    for NSSTA TPAC residential batches or mandatory iGOT certifications.
    """
    course = db.query(Course).filter(Course.id == req.course_id, Course.is_active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {req.course_id} not found."
        )

    if not req.subordinate_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one subordinate officer ID must be provided."
        )

    results: List[NominatedSubordinateResult] = []

    for sub_id in req.subordinate_ids:
        sub = db.query(User).filter(User.id == sub_id).first()
        if not sub:
            continue

        # Check authorization if not admin
        if current_user.role != "ADMIN":
            if sub.supervisor_id != current_user.id and sub.division != current_user.division:
                continue

        # Check or create enrollment
        enr = db.query(Enrollment).filter(
            Enrollment.user_id == sub.id,
            Enrollment.course_id == course.id,
        ).first()

        if enr:
            enr.status = EnrollmentStatus.ENROLLED.value
            enr.nominated_by_supervisor_id = current_user.id
            enr.enrolled_at = datetime.utcnow()
        else:
            enr = Enrollment(
                user_id=sub.id,
                course_id=course.id,
                status=EnrollmentStatus.ENROLLED.value,
                progress_percentage=0,
                nominated_by_supervisor_id=current_user.id,
                enrolled_at=datetime.utcnow(),
            )
            db.add(enr)

        db.flush()
        results.append(NominatedSubordinateResult(
            officer_id=sub.id,
            officer_name=sub.full_name,
            status="NOMINATED_ENROLLED",
            enrollment_id=enr.id,
        ))

    db.commit()

    return NominateBatchResponse(
        success=True,
        message=f"Successfully nominated {len(results)} officer(s) for '{course.title}'.",
        course_id=course.id,
        course_title=course.title,
        batch_start_date=course.batch_start_date,
        total_nominated=len(results),
        nominations=results,
    )
