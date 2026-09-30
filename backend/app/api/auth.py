from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, IGOTSSOLogin, TokenResponse, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & SSO"])

@router.post("/register", response_model=TokenResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        cadre=user_in.cadre,
        designation=user_in.designation,
        division=user_in.division,
        organization=user_in.organization,
        experience_years=user_in.experience_years,
        education=user_in.education,
        role=user_in.role or "LEARNER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role, "designation": user.designation})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "cadre": user.cadre,
            "designation": user.designation,
            "division": user.division,
            "role": user.role
        }
    }

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid official email or password."
        )

    token = create_access_token({"sub": user.email, "role": user.role, "designation": user.designation})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "cadre": user.cadre,
            "designation": user.designation,
            "division": user.division,
            "role": user.role
        }
    }

@router.post("/igot-sso", response_model=TokenResponse)
def igot_sso_login(sso_data: IGOTSSOLogin, db: Session = Depends(get_db)):
    """
    Simulates Parichay / iGOT Karmayogi Single Sign-On (SSO) authentication.
    Automatically provisions or links the civil service profile.
    """
    user = db.query(User).filter(User.email == sso_data.official_email).first()
    if not user:
        user = User(
            email=sso_data.official_email,
            hashed_password=get_password_hash("Karmayogi@2026"),
            full_name=sso_data.full_name,
            cadre=sso_data.cadre,
            designation=sso_data.designation,
            division=sso_data.division,
            organization="Ministry of Statistics & Programme Implementation (MoSPI)",
            role="LEARNER",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role, "designation": user.designation})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "cadre": user.cadre,
            "designation": user.designation,
            "division": user.division,
            "role": user.role
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)):
    """Helper for instant multi-persona demo switching during SIH presentation"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "cadre": u.cadre,
            "designation": u.designation,
            "division": u.division,
            "role": u.role,
        }
        for u in users
    ]
