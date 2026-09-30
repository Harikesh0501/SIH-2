from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class CompetencyLevelResponse(BaseModel):
    level: int
    descriptor: str
    knowledge_indicators: Optional[List[str]] = None
    skill_indicators: Optional[List[str]] = None

    class Config:
        from_attributes = True

class CompetencyResponse(BaseModel):
    id: int
    code: str
    name: str
    domain: str
    description: str
    levels: Optional[List[CompetencyLevelResponse]] = None

    class Config:
        from_attributes = True

class CompetencyGapItem(BaseModel):
    competency_id: int
    code: str
    name: str
    domain: str
    current_level: int
    required_level: int
    gap: int
    is_mandatory: bool
    weight: float
    urgency_score: float # Weighted Urgency Score
    status: str # "CRITICAL_GAP", "MODERATE_GAP", "ON_TRACK", "EXCEEDS"
    assessed_via: str

class DomainGapSummary(BaseModel):
    domain: str
    average_current_level: float
    average_required_level: float
    total_gap: int
    readiness_percentage: float # 0 - 100%

class GapAnalysisResponse(BaseModel):
    officer_name: str
    designation: str
    cadre: str
    division: str
    overall_readiness_percentage: float
    domain_summaries: List[DomainGapSummary]
    radar_data: List[Dict[str, Any]] # e.g. [{"subject": "STAT-PRICE", "current": 1, "required": 3, "fullMark": 5}]
    high_urgency_gaps: List[CompetencyGapItem]
    all_competencies: List[CompetencyGapItem]

class CareerSimulationRequest(BaseModel):
    target_designation: str

class CareerSimulationResponse(BaseModel):
    current_designation: str
    target_designation: str
    readiness_percentage: float
    projected_gaps: List[CompetencyGapItem]
    recommended_pathway_summary: List[str]

class SupervisorCalibrateRequest(BaseModel):
    subordinate_id: int
    competency_id: int
    calibrated_level: int
    justification: Optional[str] = None

class SupervisorCalibrateResponse(BaseModel):
    success: bool
    message: str
    subordinate_id: int
    subordinate_name: str
    competency_code: str
    competency_name: str
    new_level: int
    assessed_via: str
    new_readiness_percentage: float

class SubordinateCompetencyScore(BaseModel):
    competency_id: int
    code: str
    name: str
    domain: str
    current_level: int
    required_level: int
    gap: int
    status: str
    assessed_via: str

class SubordinateMatrixItem(BaseModel):
    id: int
    full_name: str
    email: str
    designation: str
    division: str
    cadre: str
    experience_years: int
    readiness_percentage: float
    critical_gaps_count: int
    moderate_gaps_count: int
    competencies: List[SubordinateCompetencyScore]

class TeamGapAggregate(BaseModel):
    competency_code: str
    competency_name: str
    domain: str
    affected_officers_count: int
    average_gap: float
    total_urgency_score: float

class TeamMatrixResponse(BaseModel):
    supervisor_id: int
    supervisor_name: str
    division: str
    total_subordinates: int
    average_team_readiness: float
    distribution: Dict[str, int]
    top_team_gaps: List[TeamGapAggregate]
    competency_columns: List[Dict[str, str]]
    subordinates: List[SubordinateMatrixItem]

