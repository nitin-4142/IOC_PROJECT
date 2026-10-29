"""
Pydantic schemas for agent inputs/outputs and API validation.
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ── Agent 1: Intelligence ────────────────────────────────────────────────────

class IncidentReportInput(BaseModel):
    raw_report: str = Field(..., min_length=10, max_length=4000)
    location_text: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_demo: bool = False


class ExtractedIncident(BaseModel):
    incident_type: str
    raw_report: str
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reported_time: Optional[str] = None
    affected_population: Optional[int] = Field(None, ge=0)
    injuries_reported: Optional[int] = Field(None, ge=0)
    missing_persons_reported: Optional[int] = Field(None, ge=0)
    immediate_threats: List[str] = Field(default_factory=list)
    extracted_facts: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    processing_source: str = "fallback"

    @field_validator("incident_type")
    @classmethod
    def validate_incident_type(cls, v: str) -> str:
        allowed = {
            "flood", "earthquake", "fire", "cyclone", "landslide",
            "building_collapse", "gas_leak", "industrial_accident",
            "tsunami", "drought", "epidemic", "other"
        }
        cleaned = v.lower().replace(" ", "_").replace("-", "_")
        return cleaned if cleaned in allowed else "other"


# ── Agent 2: Risk Assessment ─────────────────────────────────────────────────

class RiskAssessmentOutput(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: str
    contributing_factors: List[str] = Field(default_factory=list)
    rationale: str
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    requires_human_review: bool = False

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        up = v.upper()
        if up not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return up


# ── Agent 3: Resource Planning ───────────────────────────────────────────────

class ResourceItem(BaseModel):
    resource_type: str
    recommended_quantity: int = Field(..., ge=0)
    reason: str
    availability_status: str = "UNKNOWN"
    source_of_availability_data: str = "DEMO_DATA — not verified"


class ResourcePlanOutput(BaseModel):
    resources: List[ResourceItem] = Field(default_factory=list)
    notes: str = ""
    processing_source: str = "fallback"


# ── Agent 4: Logistics ───────────────────────────────────────────────────────

class RouteInfo(BaseModel):
    from_location: str
    to_location: str
    estimated_distance_km: Optional[float] = None
    estimated_time_min: Optional[float] = None
    route_status: str = "ROUTE_UNAVAILABLE"
    notes: str = ""


class LogisticsOutput(BaseModel):
    location_available: bool = False
    routes: List[RouteInfo] = Field(default_factory=list)
    nearby_shelters: List[dict] = Field(default_factory=list)
    nearby_hospitals: List[dict] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    notes: str = ""
    processing_source: str = "fallback"


# ── Agent 5: Coordination ────────────────────────────────────────────────────

class CoordinationOutput(BaseModel):
    summary: str
    priority_actions: List[str] = Field(default_factory=list)
    logistics_notes: str = ""
    resource_conflicts: List[str] = Field(default_factory=list)
    missing_data_flags: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    incident_status: str = "PLAN_READY"


# ── API I/O ──────────────────────────────────────────────────────────────────

class StatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {
            "NEW", "UNDER_REVIEW", "AWAITING_INFORMATION",
            "PLAN_READY", "APPROVED", "IN_PROGRESS", "RESOLVED", "CANCELLED"
        }
        up = v.upper()
        if up not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return up


class ApprovalRequest(BaseModel):
    operator_name: str = Field(..., min_length=1, max_length=128)
    decision: str
    notes: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"APPROVED", "REJECTED", "MODIFIED"}
        up = v.upper()
        if up not in allowed:
            raise ValueError(f"decision must be one of {allowed}")
        return up
