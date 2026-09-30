from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_supervisor
from app.models.user import User
from app.models.competency import Competency
from app.models.passport import DigitalCredential
from app.services.passport_service import PassportService

router = APIRouter(prefix="/passport", tags=["Digital Skill Passport & Credentials"])

class IssueCredentialRequest(BaseModel):
    user_id: int
    competency_code: str
    level: int
    custom_title: Optional[str] = None

@router.get("/my-passport")
def get_my_passport(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the calling officer's full MoSPI Digital Skill Passport, including:
    - Master Passport QR code
    - All verified credentials with SHA-256 cryptographic signatures
    - 4-Domain competency breakdown
    - Domain mastery badges
    - Dual-track completed courses transcript
    - Assessment history
    """
    passport_data = PassportService.get_officer_passport(db, current_user)
    return passport_data

@router.get("/officer/{user_id}")
def get_officer_passport_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows supervisors, division heads, or cadre administrators to view an officer's Digital Skill Passport.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statistical personnel with ID {user_id} not found."
        )

    # Allow access if self, or supervisor, or admin
    if current_user.id != user_id and current_user.role not in ["SUPERVISOR", "ADMIN", "TRAINER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You can only view your own passport or subordinates'."
        )

    return PassportService.get_officer_passport(db, target_user)

@router.get("/verify/{credential_code}")
def verify_credential_public(
    credential_code: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC AUDIT ENDPOINT (No authentication required).
    Verifies any MoSPI digital credential using its unique code or SHA-256 hash.
    Used when a QR code on an officer's certificate or badge is scanned.
    """
    result = PassportService.verify_credential(db, credential_code)
    if not result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result
        )
    return result

@router.get("/verify/officer/{karmayogi_id}")
def verify_officer_passport_public(
    karmayogi_id: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC AUDIT ENDPOINT (No authentication required).
    Verifies an officer's overarching Karmayogi Skill Passport by Karmayogi ID (e.g. KY-MOSPI-SSS-0004).
    """
    result = PassportService.verify_officer_passport(db, karmayogi_id)
    if not result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result
        )
    return result

@router.post("/issue")
def issue_credential(
    payload: IssueCredentialRequest,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Authorizes supervisors and faculty to issue a verified digital credential to an officer.
    """
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Officer with ID {payload.user_id} not found."
        )

    comp = db.query(Competency).filter(Competency.code == payload.competency_code).first()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competency with code {payload.competency_code} not found in MoSPI framework."
        )

    unique_code = f"MOSPI-CRED-{comp.code}-L{payload.level}-{target_user.id:04d}"
    hash_payload = f"MOSPI:{target_user.id}:{comp.code}:{payload.level}:{current_user.id}:OFFICIAL"
    sha_hash = PassportService.generate_sha256_hash(hash_payload)
    verification_url = f"http://localhost:3000/verify/{unique_code}"

    title = payload.custom_title or f"Certified Official Statistics Practitioner: {comp.name} (Level {payload.level})"

    # Check if already exists
    cred = db.query(DigitalCredential).filter(DigitalCredential.credential_code == unique_code).first()
    if not cred:
        cred = DigitalCredential(
            user_id=target_user.id,
            credential_code=unique_code,
            title=title,
            competency_code=comp.code,
            level_awarded=payload.level,
            qr_code_hash=sha_hash,
            certificate_pdf_url=f"/api/reports/officer-skill-card/{target_user.id}",
            verification_url=verification_url,
            is_verified=True,
        )
        db.add(cred)
    else:
        cred.title = title
        cred.level_awarded = payload.level
        cred.qr_code_hash = sha_hash

    db.commit()
    db.refresh(cred)

    qr_img = PassportService.generate_qr_code_base64(verification_url, box_size=5)

    return {
        "success": True,
        "message": f"Successfully issued verified credential '{unique_code}' to {target_user.full_name}.",
        "credential": {
            "id": cred.id,
            "credential_code": cred.credential_code,
            "title": cred.title,
            "competency_code": cred.competency_code,
            "level_awarded": cred.level_awarded,
            "qr_code_hash": cred.qr_code_hash,
            "verification_url": cred.verification_url,
            "qr_code_image": qr_img
        }
    }
