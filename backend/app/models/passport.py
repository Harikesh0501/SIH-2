from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DigitalCredential(Base):
    __tablename__ = "digital_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_code = Column(String(100), unique=True, index=True, nullable=False) # e.g. MOSPI-CRED-STAT-PRICE-L3
    title = Column(String(255), nullable=False)
    competency_code = Column(String(50), nullable=False)
    level_awarded = Column(Integer, default=1)
    issued_date = Column(DateTime, default=datetime.utcnow)
    qr_code_hash = Column(String(255), unique=True, index=True, nullable=False)
    certificate_pdf_url = Column(String(255), nullable=True)
    verification_url = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=True)

    user = relationship("User", back_populates="credentials")
