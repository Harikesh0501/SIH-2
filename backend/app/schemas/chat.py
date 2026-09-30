from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ChatCitation(BaseModel):
    source: str
    section: str
    relevance_score: float

class ChatMessageRequest(BaseModel):
    message: str
    session_id: str = "default"
    language: Optional[str] = None # "en", "hi", or None (auto-detect)

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    sources: Optional[List[ChatCitation]] = None
    language: str
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryItem(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    language: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: List[ChatHistoryItem]

class SuggestedPrompt(BaseModel):
    id: str
    category: str
    prompt_en: str
    prompt_hi: str
    target_competency: str

class SuggestedPromptsResponse(BaseModel):
    prompts: List[SuggestedPrompt]
