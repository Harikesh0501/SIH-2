import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class CourseSource(str, enum.Enum):
    IGOT_KARMAYOGI = "IGOT_KARMAYOGI"
    NSSTA_TPAC = "NSSTA_TPAC"

class DeliveryMode(str, enum.Enum):
    ONLINE_SELF_PACED = "ONLINE_SELF_PACED"
    RESIDENTIAL_IN_PERSON = "RESIDENTIAL_IN_PERSON"
    BLENDED = "BLENDED"

class EnrollmentStatus(str, enum.Enum):
    RECOMMENDED = "RECOMMENDED"
    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True) # e.g. IGOT-STAT-101, TPAC-2026-04
    source = Column(String(50), nullable=False) # IGOT_KARMAYOGI or NSSTA_TPAC
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    provider = Column(String(150), default="Karmayogi Bharat / NSSTA")
    duration_hours = Column(Float, default=5.0)
    delivery_mode = Column(String(50), default=DeliveryMode.ONLINE_SELF_PACED.value)
    location = Column(String(150), nullable=True) # "NSSTA Greater Noida" for residential
    target_competencies = Column(JSON, nullable=False) # list of competency codes e.g. ["STAT-PRICE", "TECH-PYST"]
    target_level = Column(Integer, default=2) # Level targeted (1 to 5)
    rating = Column(Float, default=4.8)
    thumbnail_url = Column(String(255), nullable=True)
    course_url = Column(String(255), nullable=True)
    batch_start_date = Column(String(50), nullable=True) # for TPAC residential batches
    batch_capacity = Column(Integer, default=40)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String(50), default=EnrollmentStatus.RECOMMENDED.value)
    progress_percentage = Column(Integer, default=0)
    certificate_id = Column(String(100), nullable=True)
    nominated_by_supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    nominated_by = relationship("User", foreign_keys=[nominated_by_supervisor_id])
