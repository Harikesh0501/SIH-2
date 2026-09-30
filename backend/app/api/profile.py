from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.competency import Competency, UserCompetency
from app.schemas.user import UserUpdate, UserResponse
from app.api.deps import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/profile", tags=["User Profile & Cadre Management"])

class SelfAssessmentItem(BaseModel):
    competency_code: str
    level: int # 1 to 5

class SelfAssessmentSubmission(BaseModel):
    assessments: List[SelfAssessmentItem]

@router.put("", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates the authenticated officer's profile details.
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.designation is not None:
        current_user.designation = user_update.designation
    if user_update.division is not None:
        current_user.division = user_update.division
    if user_update.experience_years is not None:
        current_user.experience_years = user_update.experience_years
    if user_update.education is not None:
        current_user.education = user_update.education

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/self-assessment")
def submit_self_assessment(
    submission: SelfAssessmentSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allows statistical personnel to record or update their self-assessed competency ratings (1 to 5).
    """
    updated_count = 0
    for item in submission.assessments:
        if item.level < 1 or item.level > 5:
            continue

        comp = db.query(Competency).filter(Competency.code == item.competency_code).first()
        if not comp:
            continue

        user_comp = db.query(UserCompetency).filter(
            UserCompetency.user_id == current_user.id,
            UserCompetency.competency_id == comp.id,
        ).first()

        if user_comp:
            user_comp.current_level = item.level
            user_comp.assessed_via = "SELF"
            user_comp.confidence_score = 0.7
            user_comp.last_evaluated_at = datetime.utcnow()
        else:
            user_comp = UserCompetency(
                user_id=current_user.id,
                competency_id=comp.id,
                current_level=item.level,
                assessed_via="SELF",
                confidence_score=0.7,
                last_evaluated_at=datetime.utcnow(),
            )
            db.add(user_comp)

        updated_count += 1

    db.commit()
    return {
        "status": "success",
        "updated_count": updated_count,
        "message": f"Successfully updated {updated_count} competency ratings for {current_user.full_name}.",
    }

@router.get("/cadre-structure")
def get_cadre_structure():
    """
    Returns standardized organizational structure for India's Official Statistical System.
    """
    return {
        "organization": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "cadres": [
            {"code": "ISS", "name": "Indian Statistical Service (Group A Gazetted)"},
            {"code": "SSS", "name": "Subordinate Statistical Service (Group B)"},
            {"code": "CONTRACTUAL", "name": "Contractual / Young Professional / Data Analyst"},
            {"code": "TRAINEE", "name": "Probationer / ISS Trainee at NSSTA"},
        ],
        "divisions": [
            {"code": "FOD", "name": "Field Operations Division (NSO)", "focus": "Nationwide primary survey data collection (PLFS, HCES, ASHE)"},
            {"code": "NAD", "name": "National Accounts Division (CSO)", "focus": "Macroeconomic aggregates, GDP compilation, GVA, SUT"},
            {"code": "ESD", "name": "Economic Statistics Division", "focus": "Consumer Price Index (CPI), IIP, Wholesale Price Monitoring"},
            {"code": "SDRD", "name": "Survey Design and Research Division", "focus": "Sampling designs, survey methodology, questionnaire drafting"},
            {"code": "SSD", "name": "Social Statistics Division", "focus": "SDG National Indicator Framework (NIF), Gender & Social statistics"},
            {"code": "DIID", "name": "Data Informatics and Innovation Division", "focus": "Big data, AI/ML, cloud infrastructure, metadata standards"},
            {"code": "NSSTA", "name": "National Statistical Systems Training Academy", "focus": "National civil service capacity building & TPAC training"},
        ],
        "designations": [
            "Junior Statistical Officer",
            "Senior Statistical Officer",
            "Assistant Director",
            "Deputy Director",
            "Joint Director",
            "Director",
            "Deputy Director General",
            "Additional Director General",
            "Director General",
        ],
    }
