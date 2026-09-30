from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.chat import ChatMessage
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatCitation,
    ChatHistoryItem,
    ChatHistoryResponse,
    SuggestedPrompt,
    SuggestedPromptsResponse,
)
from app.services.rag_engine import RAGEngine
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Sankhyiki Mitra - AI Statistical Tutor"])

# Pre-configured Official MoSPI Bilingual Prompts
OFFICIAL_SUGGESTED_PROMPTS: List[SuggestedPrompt] = [
    SuggestedPrompt(
        id="prompt-gva-gdp",
        category="National Accounts (SNA 2008)",
        prompt_en="Explain GVA at basic prices vs GDP at market prices under SNA 2008.",
        prompt_hi="SNA 2008 के तहत मूल कीमतों पर GVA और बाजार मूल्यों पर GDP में क्या अंतर है?",
        target_competency="STAT-NAS",
    ),
    SuggestedPrompt(
        id="prompt-cpi-jevons",
        category="Price Statistics & CPI",
        prompt_en="How does MoSPI calculate elementary price aggregates in CPI using the Jevons formula?",
        prompt_hi="उपभोक्ता मूल्य सूचकांक (CPI) में जेवन्स ज्यामितीय सूत्र से प्राथमिक एकत्रीकरण कैसे किया जाता है?",
        target_competency="STAT-PRICE",
    ),
    SuggestedPrompt(
        id="prompt-plfs-status",
        category="Survey Methodology & PLFS",
        prompt_en="What is the difference between Usual Principal Status (UPS) and Subsidiary Status in PLFS?",
        prompt_hi="PLFS सर्वेक्षण में सामान्य प्रमुख स्थिति (UPS) और सहायक स्थिति (UPSS) में क्या अंतर है?",
        target_competency="STAT-LABOUR",
    ),
    SuggestedPrompt(
        id="prompt-dqaf-dimensions",
        category="Quality & Governance (DQAF)",
        prompt_en="What are the five dimensions of the MoSPI Data Quality Assurance Framework (DQAF)?",
        prompt_hi="MoSPI डेटा गुणवत्ता आश्वासन रूपरेखा (DQAF) के पांच मुख्य आयाम कौन से हैं?",
        target_competency="STAT-DQAF",
    ),
    SuggestedPrompt(
        id="prompt-sut-balancing",
        category="National Accounts (SNA 2008)",
        prompt_en="How are Supply and Use Tables (SUT) balanced to resolve macroeconomic statistical discrepancy?",
        prompt_hi="आपूर्ति एवं उपयोग तालिकाओं (SUT) को संतुलित करके सांख्यिकीय विसंगति को कैसे हल किया जाता है?",
        target_competency="STAT-NAS",
    ),
    SuggestedPrompt(
        id="prompt-dpdp-act",
        category="Digital Governance & Ethics",
        prompt_en="How does the DPDP Act 2023 treat official statistical agencies as Data Fiduciaries?",
        prompt_hi="DPDP अधिनियम 2023 के तहत आधिकारिक सांख्यिकी अनुसंधान के लिए क्या छूट और सुरक्षा उपाय हैं?",
        target_competency="GOV-DPDP",
    ),
]

# 1. POST /api/chat/message
@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sends an inquiry to 'Sankhyiki Mitra', retrieving grounded MoSPI manuals context
    and generating authoritative bilingual answers with exact document citations.
    """
    clean_msg = req.message.strip()
    if not clean_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    # 1. Save user query to database
    user_msg_record = ChatMessage(
        user_id=current_user.id,
        session_id=req.session_id,
        role="user",
        content=clean_msg,
        language=req.language or RAGEngine.detect_language(clean_msg),
        created_at=datetime.utcnow(),
    )
    db.add(user_msg_record)
    db.flush()

    # 2. Generate tutoring response via RAG engine
    tutoring_result = RAGEngine.generate_tutoring_response(
        query=clean_msg,
        session_id=req.session_id,
        user_name=current_user.full_name,
        user_designation=current_user.designation,
    )

    # 3. Format citations
    citations: List[ChatCitation] = []
    citations_json = []
    for src in tutoring_result.get("sources", []):
        cit = ChatCitation(
            source=src.get("source", "Official MoSPI Manual"),
            section=src.get("section", "General Reference"),
            relevance_score=src.get("relevance_score", 1.0),
        )
        citations.append(cit)
        citations_json.append(cit.model_dump())

    # 4. Save assistant response to database
    assistant_msg_record = ChatMessage(
        user_id=current_user.id,
        session_id=req.session_id,
        role="assistant",
        content=tutoring_result["answer"],
        sources=citations_json,
        language=tutoring_result.get("language", "en"),
        created_at=datetime.utcnow(),
    )
    db.add(assistant_msg_record)
    db.commit()
    db.refresh(assistant_msg_record)

    return ChatMessageResponse(
        id=assistant_msg_record.id,
        session_id=assistant_msg_record.session_id,
        role="assistant",
        content=assistant_msg_record.content,
        sources=citations,
        language=assistant_msg_record.language,
        provider=tutoring_result.get("provider", "NVIDIA_NIM"),
        created_at=assistant_msg_record.created_at,
    )

# 2. GET /api/chat/history
@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str = Query("default", description="Chat conversation session ID"),
    limit: int = Query(50, description="Max messages to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves previous discussion threads between the authenticated officer and Sankhyiki Mitra.
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )

    items = [
        ChatHistoryItem(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            language=m.language,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return ChatHistoryResponse(
        session_id=session_id,
        total_messages=len(items),
        messages=items,
    )

# 3. DELETE /api/chat/history
@router.delete("/history")
def clear_chat_history(
    session_id: str = Query("default", description="Session ID to clear"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clears conversation history for the specified session.
    """
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.session_id == session_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"success": True, "message": f"Cleared {deleted} message(s) from session '{session_id}'."}

# 4. GET /api/chat/suggested-prompts
@router.get("/suggested-prompts", response_model=SuggestedPromptsResponse)
def get_suggested_prompts():
    """
    Returns curated, bilingual MoSPI quick prompts across National Accounts, Price Indices,
    PLFS Sampling, and DQAF Quality Framework.
    """
    return SuggestedPromptsResponse(prompts=OFFICIAL_SUGGESTED_PROMPTS)
