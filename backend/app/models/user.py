import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    LEARNER = "LEARNER"
    TRAINER = "TRAINER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"

class CadreType(str, enum.Enum):
    ISS = "ISS"           # Indian Statistical Service
    SSS = "SSS"           # Subordinate Statistical Service
    CONTRACTUAL = "CONTRACTUAL"
    OTHER = "OTHER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    cadre = Column(String(50), default=CadreType.SSS.value)
    designation = Column(String(100), default="Junior Statistical Officer")
    division = Column(String(100), default="FOD") # FOD, NAD, ESD, SDRD, SSD, DIID
    organization = Column(String(150), default="Ministry of Statistics & Programme Implementation (MoSPI)")
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    experience_years = Column(Integer, default=2)
    education = Column(String(150), default="Master's in Statistics / Economics")
    role = Column(String(50), default=UserRole.LEARNER.value)
    avatar_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supervisor = relationship("User", remote_side=[id], backref="subordinates")
    competencies = relationship("UserCompetency", back_populates="user", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", foreign_keys="[Enrollment.user_id]", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    credentials = relationship("DigitalCredential", back_populates="user", cascade="all, delete-orphan")
