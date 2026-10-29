"""
Central Orchestrator
======================
Coordinates the sequential five-agent workflow:
  Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5 → Persist → Return

Each agent result is persisted even if downstream agents fail.
Correlation IDs allow full end-to-end tracing.
"""
from __future__ import annotations
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from schemas import IncidentReportInput, ExtractedIncident, RiskAssessmentOutput, ResourcePlanOutput, LogisticsOutput, CoordinationOutput
from agents import intelligence_agent, risk_agent, resource_agent, logistics_agent, coordination_agent

logger = logging.getLogger(__name__)


class AgentResult:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.status = "PENDING"
        self.used_fallback = False
        self.duration_ms: Optional[float] = None
        self.error_message: Optional[str] = None
        self.output = None

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "used_fallback": self.used_fallback,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
        }


def _run_agent(name: str, fn, *args, **kwargs) -> AgentResult:
    """Execute a single agent with timing and error capture."""
    result = AgentResult(name)
    start = time.time()
    try:
        result.output = fn(*args, **kwargs)
        result.status = "SUCCESS"
    except Exception as exc:
        result.status = "FAILED"
        result.error_message = str(exc)
        logger.error("Agent %s failed: %s", name, exc, exc_info=True)
    finally:
        result.duration_ms = round((time.time() - start) * 1000, 2)
    return result


def _persist_incident(
    db,
    input_data: IncidentReportInput,
    incident: ExtractedIncident,
    correlation_id: str,
    is_demo: bool,
) -> "models.incident.Incident":
    from models.incident import Incident
    obj = Incident(
        correlation_id=correlation_id,
        raw_report=incident.raw_report,
        incident_type=incident.incident_type,
        location_text=incident.location_text,
        latitude=incident.latitude,
        longitude=incident.longitude,
        reported_time=incident.reported_time,
        affected_population=incident.affected_population,
        injuries_reported=incident.injuries_reported,
        missing_persons_reported=incident.missing_persons_reported,
        immediate_threats=json.dumps(incident.immediate_threats),
        extracted_facts=json.dumps(incident.extracted_facts),
        missing_information=json.dumps(incident.missing_information),
        confidence=incident.confidence,
        processing_source=incident.processing_source,
        status="PLAN_READY",
        is_demo=str(is_demo).lower(),
    )
    db.add(obj)
    db.flush()
    return obj


def _persist_risk(db, incident_id: str, risk: RiskAssessmentOutput):
    from models.assessment import RiskAssessment
    obj = RiskAssessment(
        incident_id=incident_id,
        risk_score=risk.risk_score,
        severity=risk.severity,
        contributing_factors=json.dumps(risk.contributing_factors),
        rationale=risk.rationale,
        confidence=risk.confidence,
        requires_human_review=risk.requires_human_review,
    )
    db.add(obj)


def _persist_resources(db, incident_id: str, plan: ResourcePlanOutput):
    from models.resource import ResourceRecommendation
    for r in plan.resources:
        db.add(ResourceRecommendation(
            incident_id=incident_id,
            resource_type=r.resource_type,
            recommended_quantity=r.recommended_quantity,
            reason=r.reason,
            availability_status=r.availability_status,
            source_of_availability_data=r.source_of_availability_data,
        ))


def _persist_plan(db, incident_id: str, coord: CoordinationOutput, logistics: LogisticsOutput) -> "models.plan.ResponsePlan":
    from models.plan import ResponsePlan
    plan = ResponsePlan(
        incident_id=incident_id,
        summary=coord.summary,
        priority_actions=json.dumps(coord.priority_actions),
        logistics_notes=coord.logistics_notes,
        resource_conflicts=json.dumps(coord.resource_conflicts),
        missing_data_flags=json.dumps(coord.missing_data_flags),
        follow_up_questions=json.dumps(coord.follow_up_questions),
        approval_status="PENDING",
    )
    db.add(plan)
    db.flush()
    return plan


def _persist_agent_execution(db, incident_id: str, result: AgentResult):
    from models.execution import AgentExecution
    db.add(AgentExecution(
        incident_id=incident_id,
        agent_name=result.agent_name,
        status=result.status,
        used_fallback=result.used_fallback,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
    ))


def _log_event(db, incident_id: str, event_type: str, description: str, actor: str = "system"):
    from models.execution import IncidentEvent
    db.add(IncidentEvent(
        incident_id=incident_id,
        event_type=event_type,
        description=description,
        actor=actor,
    ))


def _update_incident_status(db, incident_obj, status: str, risk: Optional[RiskAssessmentOutput] = None):
    incident_obj.status = status
    if risk:
        incident_obj.risk_score = risk.risk_score
        incident_obj.severity = risk.severity
    incident_obj.updated_at = datetime.now(timezone.utc)


def run_workflow(input_data: IncidentReportInput, db) -> dict:
    """
    Execute the full five-agent workflow.
    Returns a structured dict suitable for API response.
    """
    correlation_id = str(uuid.uuid4())
    logger.info("=== Starting workflow correlation_id=%s ===", correlation_id)
    workflow_start = time.time()

    agent_results: dict[str, AgentResult] = {}
    incident_obj = None
    incident_id = None

    # ── Agent 1: Intelligence ─────────────────────────────────────────────
    a1 = _run_agent("intelligence_agent", intelligence_agent.process, input_data)
    agent_results["intelligence_agent"] = a1

    if a1.status == "FAILED" or a1.output is None:
        return _error_response(
            correlation_id, "Agent 1 (Intelligence) failed to extract incident information.",
            agent_results, workflow_start,
        )

    incident: ExtractedIncident = a1.output
    a1.used_fallback = incident.processing_source == "fallback"

    # Persist incident and Agent 1 execution
    try:
        incident_obj = _persist_incident(db, input_data, incident, correlation_id, input_data.is_demo)
        incident_id = incident_obj.id
        _persist_agent_execution(db, incident_id, a1)
        _log_event(db, incident_id, "INCIDENT_CREATED", f"Incident created via intelligence agent ({incident.processing_source})")
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("DB persist after Agent 1 failed: %s", exc)
        return _error_response(correlation_id, f"Database error after intelligence agent: {exc}", agent_results, workflow_start)

    # ── Agent 2: Risk Assessment ──────────────────────────────────────────
    a2 = _run_agent("risk_agent", risk_agent.process, incident)
    agent_results["risk_agent"] = a2

    risk: Optional[RiskAssessmentOutput] = a2.output
    if a2.status == "FAILED" or risk is None:
        _safe_persist_execution(db, incident_id, a2)
        _mark_incident_status(db, incident_obj, "UNDER_REVIEW")
        return _partial_response(correlation_id, incident_id, incident, None, None, None, None, agent_results, workflow_start, "Agent 2 (Risk) failed")

    try:
        _persist_risk(db, incident_id, risk)
        _persist_agent_execution(db, incident_id, a2)
        _update_incident_status(db, incident_obj, incident_obj.status, risk)
        _log_event(db, incident_id, "RISK_ASSESSED", f"Risk score: {risk.risk_score:.1f} → {risk.severity}")
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("DB persist after Agent 2: %s", exc)

    # ── Agent 3: Resource Planning ────────────────────────────────────────
    a3 = _run_agent("resource_agent", resource_agent.process, incident, risk, db)
    agent_results["resource_agent"] = a3

    resource_plan: Optional[ResourcePlanOutput] = a3.output
    if a3.status == "FAILED" or resource_plan is None:
        _safe_persist_execution(db, incident_id, a3)
        resource_plan = ResourcePlanOutput(notes="Agent 3 failed — resources unavailable", processing_source="failed")

    try:
        if a3.output:
            _persist_resources(db, incident_id, resource_plan)
        _persist_agent_execution(db, incident_id, a3)
        _log_event(db, incident_id, "RESOURCES_PLANNED", f"{len(resource_plan.resources)} resource types recommended")
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("DB persist after Agent 3: %s", exc)

    # ── Agent 4: Logistics ────────────────────────────────────────────────
    a4 = _run_agent("logistics_agent", logistics_agent.process, incident, resource_plan, db)
    agent_results["logistics_agent"] = a4

    logistics: Optional[LogisticsOutput] = a4.output
    if a4.status == "FAILED" or logistics is None:
        a4.used_fallback = True
        logistics = LogisticsOutput(warnings=["Logistics agent failed — routing unavailable"], notes="Agent 4 failed")

    try:
        _persist_agent_execution(db, incident_id, a4)
        _log_event(db, incident_id, "LOGISTICS_PLANNED", f"Location available: {logistics.location_available}, routes: {len(logistics.routes)}")
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("DB persist after Agent 4: %s", exc)

    # ── Agent 5: Coordination ─────────────────────────────────────────────
    a5 = _run_agent("coordination_agent", coordination_agent.process, incident, risk, resource_plan, logistics, db)
    agent_results["coordination_agent"] = a5

    coord: Optional[CoordinationOutput] = a5.output
    if a5.status == "FAILED" or coord is None:
        coord = CoordinationOutput(
            summary="Coordination agent failed — partial plan only.",
            priority_actions=["Human operator review required — automated plan incomplete."],
            incident_status="UNDER_REVIEW",
        )

    # Persist plan and finalize
    try:
        plan_obj = _persist_plan(db, incident_id, coord, logistics)
        _persist_agent_execution(db, incident_id, a5)
        _update_incident_status(db, incident_obj, coord.incident_status, risk)
        _log_event(db, incident_id, "PLAN_READY", "Five-agent workflow completed — plan awaiting operator approval")
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Final DB commit failed: %s", exc)

    total_ms = round((time.time() - workflow_start) * 1000, 2)
    logger.info("=== Workflow done correlation_id=%s total_ms=%.0f ===", correlation_id, total_ms)

    return {
        "correlation_id": correlation_id,
        "incident_id": incident_id,
        "incident": incident.model_dump(),
        "risk_assessment": risk.model_dump() if risk else None,
        "resource_plan": resource_plan.model_dump() if resource_plan else None,
        "logistics": logistics.model_dump() if logistics else None,
        "coordination": coord.model_dump() if coord else None,
        "agent_results": {k: v.to_dict() for k, v in agent_results.items()},
        "total_duration_ms": total_ms,
        "status": "SUCCESS",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_persist_execution(db, incident_id: str, result: AgentResult):
    try:
        _persist_agent_execution(db, incident_id, result)
        db.commit()
    except Exception:
        db.rollback()


def _mark_incident_status(db, incident_obj, status: str):
    try:
        incident_obj.status = status
        db.commit()
    except Exception:
        db.rollback()


def _error_response(correlation_id: str, message: str, agent_results: dict, start: float) -> dict:
    return {
        "correlation_id": correlation_id,
        "incident_id": None,
        "error": message,
        "agent_results": {k: v.to_dict() for k, v in agent_results.items()},
        "total_duration_ms": round((time.time() - start) * 1000, 2),
        "status": "FAILED",
    }


def _partial_response(
    correlation_id, incident_id, incident, risk, resource_plan, logistics, coord,
    agent_results, start, message
) -> dict:
    return {
        "correlation_id": correlation_id,
        "incident_id": incident_id,
        "incident": incident.model_dump() if incident else None,
        "risk_assessment": risk.model_dump() if risk else None,
        "resource_plan": resource_plan.model_dump() if resource_plan else None,
        "logistics": logistics.model_dump() if logistics else None,
        "coordination": coord.model_dump() if coord else None,
        "agent_results": {k: v.to_dict() for k, v in agent_results.items()},
        "total_duration_ms": round((time.time() - start) * 1000, 2),
        "status": "PARTIAL",
        "warning": message,
    }
