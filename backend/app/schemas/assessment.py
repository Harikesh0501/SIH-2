from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class MaterialChunkResponse(BaseModel):
    id: int
    chunk_index: int
    chunk_text: str
    page_or_slide_number: Optional[int] = None
    section_title: Optional[str] = None

    class Config:
        from_attributes = True

class MaterialUploadResponse(BaseModel):
    material_id: int
    title: str
    filename: str
    file_type: str
    file_size_bytes: int
    slide_or_page_count: int
    total_chunks: int
    extracted_word_count: int
    preview_text: str
    created_at: datetime

class TranscriptIngestRequest(BaseModel):
    title: str
    description: Optional[str] = None
    transcript_text: str
    video_url: Optional[str] = None
    competency_code: Optional[str] = None

class TranscriptIngestResponse(BaseModel):
    material_id: int
    title: str
    file_type: str
    total_chunks: int
    word_count: int
    status: str
    created_at: datetime

class MaterialListItem(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size_bytes: int
    slide_or_page_count: int
    total_chunks: int
    created_at: datetime

    class Config:
        from_attributes = True

class MaterialDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    filename: str
    file_type: str
    file_size_bytes: int
    slide_or_page_count: int
    extracted_text: Optional[str] = None
    status: str
    created_at: datetime
    chunks: List[MaterialChunkResponse]

    class Config:
        from_attributes = True

class GeneratedMCQItem(BaseModel):
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: str
    citation: str
    blooms_level: str # REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE
    difficulty_level: int # 1 to 5

class MCQGenerationRequest(BaseModel):
    material_id: Optional[int] = None
    custom_context_text: Optional[str] = None
    competency_code: Optional[str] = None
    target_level: int = 2
    num_questions: int = 5
    blooms_distribution: Optional[List[str]] = None

class MCQGenerationResponse(BaseModel):
    success: bool
    quiz_id: Optional[int] = None
    source_title: str
    competency_code: Optional[str] = None
    target_level: int
    total_questions_generated: int
    generated_by: str # "NVIDIA_NIM_LLAMA_3.2" or "INTELLIGENT_HEURISTIC_FALLBACK"
    questions: List[GeneratedMCQItem]

class QuestionPublicItem(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    options: List[str]
    blooms_level: str
    difficulty_level: int

class QuizListItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    competency_code: Optional[str] = None
    target_level: int
    total_questions: int
    time_limit_minutes: int
    pass_percentage: float
    is_adaptive: bool
    attempted: bool = False
    best_score: Optional[float] = None
    created_at: datetime

class QuizDetailPublicResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    competency_code: Optional[str] = None
    target_level: int
    total_questions: int
    time_limit_minutes: int
    pass_percentage: float
    is_adaptive: bool
    created_at: datetime
    questions: List[QuestionPublicItem]

class AdaptiveNextRequest(BaseModel):
    previous_question_id: Optional[int] = None
    selected_option_index: Optional[int] = None
    current_difficulty: int = 2
    answered_question_ids: List[int] = []

class AdaptiveNextResponse(BaseModel):
    is_complete: bool
    next_question: Optional[QuestionPublicItem] = None
    current_difficulty: int
    current_theta: float
    questions_remaining: int
    feedback_on_previous: Optional[Dict[str, Any]] = None

class QuizSubmitRequest(BaseModel):
    user_answers: Dict[str, int] # e.g. {"1": 0, "2": 3}
    time_taken_seconds: int = 0
    difficulty_progression: Optional[List[Dict[str, Any]]] = None

class QuestionDiagnosticResult(BaseModel):
    question_id: int
    question_text: str
    selected_option_index: Optional[int]
    correct_option_index: int
    is_correct: bool
    explanation: str
    citation: str
    blooms_level: str
    difficulty_level: int

class QuizSubmitResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_title: str
    competency_code: Optional[str] = None
    score: float
    max_score: float
    percentage: float
    passed: bool
    time_taken_seconds: int
    competency_promoted: bool
    previous_level: Optional[int] = None
    new_level: Optional[int] = None
    new_readiness_percentage: float
    blooms_performance: Dict[str, Dict[str, Any]]
    remedial_recommendations: List[str]
    question_results: List[QuestionDiagnosticResult]



