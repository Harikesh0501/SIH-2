import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_supervisor, require_admin
from app.models.user import User
from app.services.pdf_report_service import PDFReportService

router = APIRouter(prefix="/reports", tags=["Official PDF Reports & Dossiers"])

@router.get("/officer-skill-card/{user_id}")
def download_officer_skill_card(
    user_id: int,
    inline: bool = Query(False, description="Set true to display inline in browser instead of attachment download"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates and downloads the official MoSPI Officer Digital Skill Card (PDF).
    Features:
    - National Emblem and MoSPI / NSSTA official banner
    - Officer identification, Karmayogi ID, cadre, and division
    - Embedded scannable Black & White QR code linking to verification portal
    - Competency proficiency matrix across all 4 domains
    - Issued micro-credentials with SHA-256 tamper-evident signatures
    - Official NSSTA Director General signatory endorsement
    """
    target_id = current_user.id if user_id == 0 else user_id
    target_user = db.query(User).filter(User.id == target_id).first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statistical personnel with ID {user_id} not found."
        )

    # Permission: officer can view self, supervisor/admin can view subordinates
    if current_user.id != target_user.id and current_user.role not in ["SUPERVISOR", "ADMIN", "TRAINER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted. You may only download your own skill card or subordinates'."
        )

    pdf_bytes = PDFReportService.generate_officer_skill_card(db, target_user)
    disposition = "inline" if inline else "attachment"
    filename = f"mospi_skill_card_{target_user.cadre}_{target_user.id:04d}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/ministry-capacity-readiness")
def download_ministry_readiness_report(
    inline: bool = Query(False, description="Set true to display inline in browser instead of attachment download"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates and downloads the Annual Cadre Competency Readiness & TPAC Allocation Dossier (PDF).
    Features:
    - Executive Macro Metrics: total assessed personnel, cadre health index, training nominations
    - Division Competency Gap Matrix: FOD, NAD, ESD, SDRD, DPD readiness vs role benchmarks
    - Top 5 Systemic Workforce Bottlenecks evaluated with Weighted Urgency Scoring (WUS)
    - NSSTA TPAC Residential Training Allocation & Cohort Nominations (2026-27)
    - Statutory review block for Training Programme Approval Committee
    """
    pdf_bytes = PDFReportService.generate_ministry_readiness_report(db)
    disposition = "inline" if inline else "attachment"
    filename = "mospi_tpac_capacity_readiness_report_2026.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
