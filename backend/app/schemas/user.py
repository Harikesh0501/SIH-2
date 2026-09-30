from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    EmailStr = str

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    cadre: Optional[str] = "SSS"
    designation: Optional[str] = "Junior Statistical Officer"
    division: Optional[str] = "FOD"
    organization: Optional[str] = "Ministry of Statistics & Programme Implementation (MoSPI)"
    experience_years: Optional[int] = 2
    education: Optional[str] = "Master's in Statistics / Economics"
    role: Optional[str] = "LEARNER"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class IGOTSSOLogin(BaseModel):
    civil_service_id: str
    official_email: EmailStr
    full_name: str
    cadre: str
    designation: str
    division: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    division: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(UserBase):
    id: int
    supervisor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
