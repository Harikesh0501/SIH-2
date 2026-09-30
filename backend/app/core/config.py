import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./karmayogi.db"
    
    # NVIDIA NIM LLM Model (Nemotron Ultra)
    NVIDIA_API_KEY: Optional[str] = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    
    # Fallback Gemini (Optional)
    GEMINI_API_KEY: Optional[str] = ""
    
    # Security & Tokens
    SECRET_KEY: str = "karmayogi_sankhyiki_secret_key_sih26101_secure_token_salt_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # iGOT Karmayogi Simulation
    IGOT_API_BASE_URL: str = "https://igotkarmayogi.gov.in/api/v1"
    IGOT_MOCK_MODE: bool = True
    PUBLIC_VERIFY_BASE_URL: str = "http://localhost:3000/verify"
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    REPORT_DIR: str = os.path.join(BASE_DIR, "reports")

    @property
    def get_database_url(self) -> str:
        url = self.DATABASE_URL
        # Normalize postgres:// and postgresql:// to postgresql+psycopg2:// for SQLAlchemy
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        if not os.path.exists(env_file):
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
