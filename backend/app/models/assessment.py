import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class BloomsLevel(str, enum.Enum):
    REMEMBER = "REMEMBER"       # Knowledge / Recall
    UNDERSTAND = "UNDERSTAND"   # Comprehension
    APPLY = "APPLY"             # Calculation / Application
    ANALYZE = "ANALYZE"         # Data dissection / Anomaly detection
    EVALUATE = "EVALUATE"       # Quality check / Critical decision

class LearningMaterial(Base):
    __tablename__ = "learning_materials"

    id = Column(Integer, primary_key=True, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), default="pdf") # pdf, docx, pptx, transcript
    file_size_bytes = Column(Integer, default=0)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    slide_or_page_count = Column(Integer, default=0)
    status = Column(String(50), default="READY") # PENDING, PROCESSING, READY, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("MaterialChunk", back_populates="material", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="material")

class MaterialChunk(Base):
    __tablename__ = "material_chunks"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("learning_materials.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    page_or_slide_number = Column(Integer, nullable=True)
    section_title = Column(String(255), nullable=True)

    material = relationship("LearningMaterial", back_populates="chunks")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("learning_materials.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    competency_code = Column(String(50), nullable=True) # Tagged competency e.g. STAT-PRICE
    target_level = Column(Integer, default=2) # 1 to 5
    total_questions = Column(Integer, default=5)
    time_limit_minutes = Column(Integer, default=15)
    pass_percentage = Column(Float, default=70.0)
    is_adaptive = Column(Boolean, default=True) # Computerized Adaptive Testing (CAT)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("LearningMaterial", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # list of string options e.g. ["Option A", "Option B", ...]
    correct_option_index = Column(Integer, nullable=False) # 0, 1, 2, or 3
    explanation = Column(Text, nullable=False) # Detailed explanation why the answer is correct
    citation = Column(String(255), nullable=True) # e.g. "Chapter 3, Page 14, Para 2" or "Slide 12"
    blooms_level = Column(String(50), default=BloomsLevel.UNDERSTAND.value)
    difficulty_level = Column(Integer, default=2) # 1 to 5

    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    time_taken_seconds = Column(Integer, default=0)
    user_answers = Column(JSON, nullable=True) # { "question_id": selected_option_index }
    difficulty_progression = Column(JSON, nullable=True) # list of difficulty levels recorded per question
    created_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
