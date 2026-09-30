import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class CompetencyDomain(str, enum.Enum):
    STATISTICAL = "STATISTICAL"
    TECHNICAL = "TECHNICAL"
    DIGITAL_GOVERNANCE = "DIGITAL_GOVERNANCE"
    BEHAVIOURAL_MANAGERIAL = "BEHAVIOURAL_MANAGERIAL"

class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # e.g. STAT-SURV, STAT-NAS, TECH-PYST
    name = Column(String(255), nullable=False)
    domain = Column(String(50), nullable=False) # STATISTICAL, TECHNICAL, etc.
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    levels = relationship("CompetencyLevel", back_populates="competency", cascade="all, delete-orphan")
    role_benchmarks = relationship("RoleBenchmark", back_populates="competency", cascade="all, delete-orphan")
    user_competencies = relationship("UserCompetency", back_populates="competency", cascade="all, delete-orphan")

class CompetencyLevel(Base):
    __tablename__ = "competency_levels"

    id = Column(Integer, primary_key=True, index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    level = Column(Integer, nullable=False) # 1 to 5
    descriptor = Column(String(255), nullable=False)
    knowledge_indicators = Column(JSON, nullable=True) # list of knowledge points
    skill_indicators = Column(JSON, nullable=True)     # list of skill points

    competency = relationship("Competency", back_populates="levels")

class RoleBenchmark(Base):
    __tablename__ = "role_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    designation = Column(String(100), index=True, nullable=False) # Junior Statistical Officer, Senior Statistical Officer, etc.
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_level = Column(Integer, nullable=False) # 1 to 5
    is_mandatory = Column(Boolean, default=True)
    weight = Column(Float, default=1.0) # Criticality multiplier (1.0 - 2.0)

    competency = relationship("Competency", back_populates="role_benchmarks")

class UserCompetency(Base):
    __tablename__ = "user_competencies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    current_level = Column(Integer, default=1) # 1 to 5
    assessed_via = Column(String(50), default="SELF") # SELF, SUPERVISOR, QUIZ, IGOT
    confidence_score = Column(Float, default=0.5) # 0.0 to 1.0
    last_evaluated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="competencies")
    competency = relationship("Competency", back_populates="user_competencies")
