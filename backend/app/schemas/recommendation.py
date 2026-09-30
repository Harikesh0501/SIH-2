from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class RecommendedCourseItem(BaseModel):
    course_id: int
    external_id: str
    source: str # IGOT_KARMAYOGI or NSSTA_TPAC
    title: str
    description: str
    provider: str
    duration_hours: float
    delivery_mode: str
    location: Optional[str] = None
    rating: float
    thumbnail_url: Optional[str] = None
    course_url: Optional[str] = None
    batch_start_date: Optional[str] = None
    batch_capacity: Optional[int] = None
    target_competencies: List[str]
    target_level: int
    relevance_score: float # 0.0 - 100.0%
    bridged_gap_code: str
    bridged_gap_name: str
    bridged_gap_urgency: float
    recommendation_rationale: str
    enrollment_status: str # "NOT_ENROLLED", "RECOMMENDED", "ENROLLED", "IN_PROGRESS", "COMPLETED"
    progress_percentage: int
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PathwayResponse(BaseModel):
    officer_name: str
    designation: str
    division: str
    cadre: str
    overall_readiness_percentage: float
    critical_gaps_count: int
    track_a_igot_courses: List[RecommendedCourseItem]
    track_b_tpac_courses: List[RecommendedCourseItem]
    all_recommendations: List[RecommendedCourseItem]

class EnrollCourseRequest(BaseModel):
    course_id: int

class EnrollCourseResponse(BaseModel):
    success: bool
    message: str
    enrollment_id: int
    course_id: int
    course_title: str
    source: str
    status: str
    enrolled_at: datetime
    igot_deep_link: Optional[str] = None

class CompleteWebhookRequest(BaseModel):
    user_email: str
    course_external_id: str
    score_percentage: float
    completion_date: Optional[str] = None
    certificate_id: Optional[str] = None

class CompleteWebhookResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    user_name: str
    course_title: str
    status: str
    upgraded_competencies: List[Dict[str, Any]]
    new_readiness_percentage: float

class NominateBatchRequest(BaseModel):
    course_id: int
    subordinate_ids: List[int]
    justification: Optional[str] = None

class NominatedSubordinateResult(BaseModel):
    officer_id: int
    officer_name: str
    status: str
    enrollment_id: int

class NominateBatchResponse(BaseModel):
    success: bool
    message: str
    course_id: int
    course_title: str
    batch_start_date: Optional[str]
    total_nominated: int
    nominations: List[NominatedSubordinateResult]

class EnrollmentItem(BaseModel):
    enrollment_id: int
    course_id: int
    external_id: str
    source: str
    title: str
    description: str
    provider: str
    duration_hours: float
    delivery_mode: str
    location: Optional[str] = None
    target_competencies: List[str]
    target_level: int
    status: str
    progress_percentage: int
    certificate_id: Optional[str] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    nominated_by_name: Optional[str] = None
    course_url: Optional[str] = None

class MyCoursesResponse(BaseModel):
    total_enrolled: int
    in_progress_count: int
    completed_count: int
    courses: List[EnrollmentItem]

