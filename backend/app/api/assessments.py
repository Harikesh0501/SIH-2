from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.assessment import LearningMaterial, MaterialChunk, Quiz, Question, QuizAttempt
from app.models.competency import Competency, UserCompetency
from app.schemas.assessment import (
    MaterialUploadResponse,
    TranscriptIngestRequest,
    TranscriptIngestResponse,
    MaterialListItem,
    MaterialDetailResponse,
    MaterialChunkResponse,
    MCQGenerationRequest,
    MCQGenerationResponse,
    GeneratedMCQItem,
    QuestionPublicItem,
    QuizListItem,
    QuizDetailPublicResponse,
    AdaptiveNextRequest,
    AdaptiveNextResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuestionDiagnosticResult,
)
from app.services.document_parser import DocumentParser
from app.services.mcq_generator import MCQGenerator
from app.services.gap_analyzer import CompetencyGapAnalyzer
from app.api.deps import get_current_user

router = APIRouter(prefix="/assessments", tags=["Multimodal Assessments & Material Ingestion"])

STORAGE_DIR = os.path.join(os.getcwd(), "storage", "uploads")
os.makedirs(STORAGE_DIR, exist_ok=True)

# 1. POST /api/assessments/upload-material
@router.post("/upload-material", response_model=MaterialUploadResponse)
async def upload_material(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Multimodal learning material upload supporting PDF, DOCX, PPTX, and TXT documents.
    Extracts text, preserves slide numbers and section hierarchies, and performs semantic chunking.
    """
    original_name = file.filename or "uploaded_document"
    ext = os.path.splitext(original_name)[1].lower()

    allowed_extensions = {".pdf", ".docx", ".pptx", ".txt"}
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: PDF, DOCX, PPTX, TXT."
        )

    # Save file to local storage
    saved_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"
    file_path = os.path.join(STORAGE_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    # Parse based on extension
    try:
        if ext == ".pdf":
            full_text, unit_count, units_metadata = DocumentParser.parse_pdf(file_path)
            file_type = "pdf"
        elif ext == ".pptx":
            full_text, unit_count, units_metadata = DocumentParser.parse_pptx(file_path)
            file_type = "pptx"
        elif ext == ".docx":
            full_text, unit_count, units_metadata = DocumentParser.parse_docx(file_path)
            file_type = "docx"
        else: # .txt
            full_text, unit_count, units_metadata = DocumentParser.parse_txt(file_path)
            file_type = "txt"
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse {ext.upper()} document: {str(e)}"
        )

    # Perform semantic chunking
    chunks_data = DocumentParser.chunk_extracted_content(units_metadata)

    # Create LearningMaterial record
    doc_title = title.strip() if title and title.strip() else original_name
    material = LearningMaterial(
        uploader_id=current_user.id,
        title=doc_title,
        description=description or f"Official statistical material ({ext.upper()}) uploaded for automated assessment generation.",
        filename=original_name,
        file_type=file_type,
        file_size_bytes=file_size,
        file_path=file_path,
        extracted_text=full_text,
        slide_or_page_count=unit_count,
        status="READY",
    )
    db.add(material)
    db.flush()

    # Add chunks
    for ch in chunks_data:
        chunk_obj = MaterialChunk(
            material_id=material.id,
            chunk_index=ch["chunk_index"],
            chunk_text=ch["chunk_text"],
            page_or_slide_number=ch["page_or_slide_number"],
            section_title=ch["section_title"],
        )
        db.add(chunk_obj)

    db.commit()
    db.refresh(material)

    words = len(full_text.split())
    preview = " ".join(full_text.split()[:50]) + "..." if words > 50 else full_text

    return MaterialUploadResponse(
        material_id=material.id,
        title=material.title,
        filename=material.filename,
        file_type=material.file_type,
        file_size_bytes=material.file_size_bytes,
        slide_or_page_count=material.slide_or_page_count,
        total_chunks=len(chunks_data),
        extracted_word_count=words,
        preview_text=preview,
        created_at=material.created_at,
    )

# 2. POST /api/assessments/ingest-transcript
@router.post("/ingest-transcript", response_model=TranscriptIngestResponse)
def ingest_transcript(
    payload: TranscriptIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ingests video, webinar, or audio transcripts with timestamp parsing and speaker chunking.
    """
    if not payload.transcript_text or len(payload.transcript_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is too short. Minimum 50 characters required."
        )

    # Parse and chunk transcript
    full_text, seg_count, segments = DocumentParser.parse_transcript(payload.transcript_text, payload.video_url)
    chunks_data = DocumentParser.chunk_extracted_content(segments)

    # Save transcript file
    saved_filename = f"transcript_{uuid.uuid4().hex[:8]}.txt"
    file_path = os.path.join(STORAGE_DIR, saved_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    file_size = os.path.getsize(file_path)

    material = LearningMaterial(
        uploader_id=current_user.id,
        title=payload.title,
        description=payload.description or f"Webinar/lecture transcript. Source: {payload.video_url or 'Live Training Session'}",
        filename=saved_filename,
        file_type="transcript",
        file_size_bytes=file_size,
        file_path=file_path,
        extracted_text=full_text,
        slide_or_page_count=seg_count,
        status="READY",
    )
    db.add(material)
    db.flush()

    for ch in chunks_data:
        chunk_obj = MaterialChunk(
            material_id=material.id,
            chunk_index=ch["chunk_index"],
            chunk_text=ch["chunk_text"],
            page_or_slide_number=ch["page_or_slide_number"],
            section_title=ch["section_title"],
        )
        db.add(chunk_obj)

    db.commit()
    db.refresh(material)

    return TranscriptIngestResponse(
        material_id=material.id,
        title=material.title,
        file_type=material.file_type,
        total_chunks=len(chunks_data),
        word_count=len(full_text.split()),
        status="READY",
        created_at=material.created_at,
    )

# 3. GET /api/assessments/materials
@router.get("/materials", response_model=List[MaterialListItem])
def list_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all uploaded statistical learning materials and training decks in the repository.
    """
    materials = db.query(LearningMaterial).order_by(LearningMaterial.created_at.desc()).all()
    results: List[MaterialListItem] = []

    for m in materials:
        results.append(MaterialListItem(
            id=m.id,
            title=m.title,
            filename=m.filename,
            file_type=m.file_type,
            file_size_bytes=m.file_size_bytes,
            slide_or_page_count=m.slide_or_page_count,
            total_chunks=len(m.chunks),
            created_at=m.created_at,
        ))

    return results

# 4. GET /api/assessments/materials/{id}
@router.get("/materials/{id}", response_model=MaterialDetailResponse)
def get_material_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns detailed content and structured semantic chunks for an uploaded learning material.
    """
    material = db.query(LearningMaterial).filter(LearningMaterial.id == id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning material with ID {id} not found."
        )

    chunks = [
        MaterialChunkResponse(
            id=ch.id,
            chunk_index=ch.chunk_index,
            chunk_text=ch.chunk_text,
            page_or_slide_number=ch.page_or_slide_number,
            section_title=ch.section_title,
        )
        for ch in sorted(material.chunks, key=lambda x: x.chunk_index)
    ]

    return MaterialDetailResponse(
        id=material.id,
        title=material.title,
        description=material.description,
        filename=material.filename,
        file_type=material.file_type,
        file_size_bytes=material.file_size_bytes,
        slide_or_page_count=material.slide_or_page_count,
        extracted_text=material.extracted_text,
        status=material.status,
        created_at=material.created_at,
        chunks=chunks,
    )

# 5. POST /api/assessments/generate-quiz
@router.post("/generate-quiz", response_model=MCQGenerationResponse)
def generate_quiz(
    req: MCQGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI-Powered Assessment & MCQ Generator.
    Uses NVIDIA NIM (meta/llama-3.2-11b-vision-instruct) with Bloom's Taxonomy cognitive
    stratification, authentic statistical distractors, and exact source citations.
    Features an automatic offline heuristic fallback.
    """
    source_title = "Custom Training Material"
    context_text = ""

    if req.material_id:
        material = db.query(LearningMaterial).filter(LearningMaterial.id == req.material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Learning material with ID {req.material_id} not found."
            )
        source_title = material.title
        context_text = material.extracted_text or ""
    elif req.custom_context_text and req.custom_context_text.strip():
        context_text = req.custom_context_text.strip()
        source_title = "Custom Statistical Concept Text"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'material_id' or non-empty 'custom_context_text' must be provided."
        )

    if len(context_text.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Context text is too short to generate quality assessment questions (minimum 30 characters required)."
        )

    # Generate MCQs using AI engine or smart fallback
    questions, generator_provider = MCQGenerator.generate_mcqs(
        context_text=context_text,
        source_title=source_title,
        competency_code=req.competency_code or "STAT-PRICE",
        target_level=req.target_level,
        num_questions=req.num_questions,
        blooms_distribution=req.blooms_distribution,
    )

    # Create Quiz record in database
    quiz = Quiz(
        material_id=req.material_id,
        title=f"Assessment: {source_title[:60]}",
        description=f"AI-generated adaptive assessment aligned with Bloom's Taxonomy for Level {req.target_level}.",
        competency_code=req.competency_code or "STAT-PRICE",
        target_level=req.target_level,
        total_questions=len(questions),
        time_limit_minutes=max(5, len(questions) * 2),
        pass_percentage=75.0,
        is_adaptive=True,
    )
    db.add(quiz)
    db.flush()

    # Add generated questions to Quiz
    for q in questions:
        question_record = Question(
            quiz_id=quiz.id,
            question_text=q.question_text,
            options=q.options,
            correct_option_index=q.correct_option_index,
            explanation=q.explanation,
            citation=q.citation,
            blooms_level=q.blooms_level,
            difficulty_level=q.difficulty_level,
        )
        db.add(question_record)

    db.commit()
    db.refresh(quiz)

    return MCQGenerationResponse(
        success=True,
        quiz_id=quiz.id,
        source_title=source_title,
        competency_code=req.competency_code,
        target_level=req.target_level,
        total_questions_generated=len(questions),
        generated_by=generator_provider,
        questions=questions,
    )

# 6. GET /api/assessments/quizzes
@router.get("/quizzes", response_model=List[QuizListItem])
def list_quizzes(
    competency_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists diagnostic, practice, and adaptive competency quizzes available in the platform.
    """
    query = db.query(Quiz).order_by(Quiz.created_at.desc())
    if competency_code:
        query = query.filter(Quiz.competency_code == competency_code)
    quizzes = query.all()

    user_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == current_user.id).all()
    attempt_map: Dict[int, List[QuizAttempt]] = {}
    for a in user_attempts:
        if a.quiz_id not in attempt_map:
            attempt_map[a.quiz_id] = []
        attempt_map[a.quiz_id].append(a)

    results: List[QuizListItem] = []
    for q in quizzes:
        attempts = attempt_map.get(q.id, [])
        has_attempted = len(attempts) > 0
        best = max([a.percentage for a in attempts]) if has_attempted else None

        results.append(QuizListItem(
            id=q.id,
            title=q.title,
            description=q.description,
            competency_code=q.competency_code,
            target_level=q.target_level,
            total_questions=q.total_questions or len(q.questions),
            time_limit_minutes=q.time_limit_minutes,
            pass_percentage=q.pass_percentage,
            is_adaptive=q.is_adaptive,
            attempted=has_attempted,
            best_score=best,
            created_at=q.created_at,
        ))

    return results

# 7. GET /api/assessments/quizzes/{id}
@router.get("/quizzes/{id}", response_model=QuizDetailPublicResponse)
def get_quiz_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns quiz details and test questions for a candidate with answers securely hidden.
    """
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {id} not found."
        )

    public_questions = [
        QuestionPublicItem(
            id=q.id,
            quiz_id=q.quiz_id,
            question_text=q.question_text,
            options=q.options,
            blooms_level=q.blooms_level,
            difficulty_level=q.difficulty_level,
        )
        for q in sorted(quiz.questions, key=lambda x: x.id)
    ]

    return QuizDetailPublicResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        competency_code=quiz.competency_code,
        target_level=quiz.target_level,
        total_questions=len(public_questions),
        time_limit_minutes=quiz.time_limit_minutes,
        pass_percentage=quiz.pass_percentage,
        is_adaptive=quiz.is_adaptive,
        created_at=quiz.created_at,
        questions=public_questions,
    )

# 8. POST /api/assessments/quizzes/{id}/adaptive-next
@router.post("/quizzes/{id}/adaptive-next", response_model=AdaptiveNextResponse)
def adaptive_next_question(
    id: int,
    req: AdaptiveNextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computerized Adaptive Testing (CAT) dynamic item selection engine.
    Evaluates previous candidate response and dynamically adapts next question's cognitive difficulty.
    """
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {id} not found."
        )

    current_diff = req.current_difficulty
    feedback = None

    if req.previous_question_id is not None and req.selected_option_index is not None:
        prev_q = db.query(Question).filter(Question.id == req.previous_question_id).first()
        if prev_q:
            was_correct = (req.selected_option_index == prev_q.correct_option_index)
            feedback = {
                "question_id": prev_q.id,
                "is_correct": was_correct,
                "explanation": prev_q.explanation,
                "citation": prev_q.citation,
            }
            if was_correct:
                current_diff = min(5, current_diff + 1)
            else:
                current_diff = max(1, current_diff - 1)

    # Find unanswered questions in this quiz
    answered_set = set(req.answered_question_ids)
    if req.previous_question_id:
        answered_set.add(req.previous_question_id)

    remaining = [q for q in quiz.questions if q.id not in answered_set]

    if not remaining:
        theta = round((current_diff - 3) * 0.75, 2)
        return AdaptiveNextResponse(
            is_complete=True,
            next_question=None,
            current_difficulty=current_diff,
            current_theta=theta,
            questions_remaining=0,
            feedback_on_previous=feedback,
        )

    # Pick question closest to current_diff
    remaining.sort(key=lambda x: abs(x.difficulty_level - current_diff))
    selected_q = remaining[0]

    theta = round((current_diff - 3) * 0.75, 2)
    next_pub = QuestionPublicItem(
        id=selected_q.id,
        quiz_id=selected_q.quiz_id,
        question_text=selected_q.question_text,
        options=selected_q.options,
        blooms_level=selected_q.blooms_level,
        difficulty_level=selected_q.difficulty_level,
    )

    return AdaptiveNextResponse(
        is_complete=False,
        next_question=next_pub,
        current_difficulty=current_diff,
        current_theta=theta,
        questions_remaining=len(remaining) - 1,
        feedback_on_previous=feedback,
    )

# 9. POST /api/assessments/quizzes/{id}/submit
@router.post("/quizzes/{id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    id: int,
    req: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits quiz attempt, computes scores, performs dynamic competency level promotion (score >= 75%),
    and outputs detailed Bloom's diagnostic feedback report.
    """
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {id} not found."
        )

    questions = {q.id: q for q in quiz.questions}
    total_q = len(questions)
    if total_q == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz has no questions configured."
        )

    correct_count = 0
    question_results: List[QuestionDiagnosticResult] = []
    blooms_tracker: Dict[str, Dict[str, int]] = {}
    missed_topics: List[str] = []

    for q_id, q_obj in questions.items():
        b_lvl = q_obj.blooms_level or "UNDERSTAND"
        if b_lvl not in blooms_tracker:
            blooms_tracker[b_lvl] = {"correct": 0, "total": 0}
        blooms_tracker[b_lvl]["total"] += 1

        user_sel = req.user_answers.get(str(q_id), req.user_answers.get(q_id))
        is_corr = (user_sel == q_obj.correct_option_index) if user_sel is not None else False

        if is_corr:
            correct_count += 1
            blooms_tracker[b_lvl]["correct"] += 1
        else:
            missed_topics.append(q_obj.citation or q_obj.question_text[:50])

        question_results.append(QuestionDiagnosticResult(
            question_id=q_obj.id,
            question_text=q_obj.question_text,
            selected_option_index=user_sel,
            correct_option_index=q_obj.correct_option_index,
            is_correct=is_corr,
            explanation=q_obj.explanation,
            citation=q_obj.citation,
            blooms_level=b_lvl,
            difficulty_level=q_obj.difficulty_level,
        ))

    score_pct = round((correct_count / total_q) * 100, 1)
    is_passed = score_pct >= quiz.pass_percentage

    # Save QuizAttempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=float(correct_count),
        max_score=float(total_q),
        percentage=score_pct,
        passed=is_passed,
        time_taken_seconds=req.time_taken_seconds,
        user_answers=req.user_answers,
        difficulty_progression=req.difficulty_progression,
    )
    db.add(attempt)

    # Dynamic Competency Upgrading (>= 75%)
    promoted = False
    old_level = None
    new_level = None

    if is_passed and quiz.competency_code:
        comp = db.query(Competency).filter(Competency.code == quiz.competency_code).first()
        if comp:
            uc = db.query(UserCompetency).filter(
                UserCompetency.user_id == current_user.id,
                UserCompetency.competency_id == comp.id,
            ).first()

            old_level = uc.current_level if uc else 1
            target_lvl = quiz.target_level

            if old_level < target_lvl:
                promoted = True
                new_level = target_lvl
                if uc:
                    uc.current_level = new_level
                    uc.assessed_via = "QUIZ"
                    uc.confidence_score = 0.95
                    uc.last_evaluated_at = datetime.utcnow()
                else:
                    uc = UserCompetency(
                        user_id=current_user.id,
                        competency_id=comp.id,
                        current_level=new_level,
                        assessed_via="QUIZ",
                        confidence_score=0.95,
                        last_evaluated_at=datetime.utcnow(),
                    )
                    db.add(uc)

    db.commit()
    db.refresh(attempt)

    # Format Bloom's performance
    blooms_perf_formatted: Dict[str, Dict[str, Any]] = {}
    for b_name, b_data in blooms_tracker.items():
        b_total = b_data["total"]
        b_corr = b_data["correct"]
        b_pct = round((b_corr / b_total) * 100, 1) if b_total > 0 else 0.0
        blooms_perf_formatted[b_name] = {
            "correct": b_corr,
            "total": b_total,
            "percentage": b_pct,
        }

    # Build remedial recommendations
    remedials: List[str] = []
    if missed_topics:
        for topic in missed_topics[:3]:
            remedials.append(f"Review official guideline: '{topic}'")
        remedials.append("Consult iGOT Karmayogi recommended micro-course for foundational reinforcement.")
    else:
        remedials.append("Outstanding mastery! You demonstrated 100% precision across all cognitive levels.")

    # Recalculate officer readiness
    new_gap = CompetencyGapAnalyzer.analyze_gaps(db, current_user)

    return QuizSubmitResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        competency_code=quiz.competency_code,
        score=float(correct_count),
        max_score=float(total_q),
        percentage=score_pct,
        passed=is_passed,
        time_taken_seconds=req.time_taken_seconds,
        competency_promoted=promoted,
        previous_level=old_level,
        new_level=new_level,
        new_readiness_percentage=new_gap.overall_readiness_percentage,
        blooms_performance=blooms_perf_formatted,
        remedial_recommendations=remedials,
        question_results=question_results,
    )


