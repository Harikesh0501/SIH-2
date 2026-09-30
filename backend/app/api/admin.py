from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_supervisor, require_admin
from app.models.user import User
from app.services.cadre_analytics_service import CadreAnalyticsService
from app.services.tpac_allocation_engine import TPACAllocationEngine

router = APIRouter(prefix="/admin", tags=["Ministry Admin & TPAC Analytics"])

class AllocateBatchRequest(BaseModel):
    course_id: int
    user_ids: List[int]
    notification_message: Optional[str] = "Official nomination confirmed for NSSTA Residential Programme. Please report to NSSTA Greater Noida as per schedule."

@router.get("/dashboard")
def get_admin_dashboard(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Unified Executive Cadre Analytics & TPAC Dashboard delivering:
    - Macro cadre health metrics & coverage
    - Division competency gap matrix (FOD, NAD, ESD, SDRD, DPD)
    - Top 5 systemic workforce bottlenecks with WUS scores
    - Live TPAC residential batch allocation queues and capacity utilization
    """
    macro_metrics = CadreAnalyticsService.get_macro_cadre_metrics(db)
    division_matrix = CadreAnalyticsService.get_division_gap_matrix(db)
    top_bottlenecks = CadreAnalyticsService.get_systemic_bottlenecks(db, top_n=5)
    tpac_batches = TPACAllocationEngine.get_all_tpac_batches(db)

    return {
        "status": "success",
        "current_admin": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "division": current_user.division
        },
        "macro_metrics": macro_metrics,
        "division_matrix": division_matrix,
        "top_bottlenecks": top_bottlenecks,
        "tpac_batches": tpac_batches,
        "quick_actions": [
            {"action": "ALLOCATE_TPAC_BATCH", "endpoint": "POST /api/admin/allocate-batch"},
            {"action": "EXPORT_TPAC_REPORT_PDF", "endpoint": "GET /api/reports/ministry-capacity-readiness"},
            {"action": "CALIBRATE_SUBORDINATES", "endpoint": "POST /api/competencies/supervisor-calibrate"}
        ]
    }

@router.get("/cadre-analytics")
def get_cadre_analytics(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Detailed macro analytics on workforce readiness, cadre distribution, and domain health.
    """
    return CadreAnalyticsService.get_macro_cadre_metrics(db)

@router.get("/division-heatmaps")
def get_division_heatmaps(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Detailed division-wise competency matrix and 5x4 heatmap grid for Recharts visualization.
    """
    return CadreAnalyticsService.get_division_gap_matrix(db)

@router.get("/bottlenecks")
def get_systemic_bottlenecks(
    top_n: int = 5,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Identifies top systemic competency bottlenecks across all statistical personnel using WUS.
    """
    return {
        "top_bottlenecks": CadreAnalyticsService.get_systemic_bottlenecks(db, top_n=top_n)
    }

@router.get("/tpac-batches")
def get_tpac_batches(
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Lists all active NSSTA TPAC residential training batches with AI recommended candidate queues.
    """
    return {
        "tpac_batches": TPACAllocationEngine.get_all_tpac_batches(db)
    }

@router.post("/allocate-batch")
def allocate_tpac_batch(
    payload: AllocateBatchRequest,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Confirms batch nominations for statistical personnel to an upcoming NSSTA residential training batch.
    Dispatches training alerts and updates enrollment records.
    """
    try:
        result = TPACAllocationEngine.allocate_batch_nominations(
            db=db,
            course_id=payload.course_id,
            user_ids=payload.user_ids,
            admin_user=current_user,
            message=payload.notification_message
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
