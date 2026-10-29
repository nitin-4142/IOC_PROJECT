"""
Flask REST API routes for the AI Disaster Response Coordinator.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from sqlalchemy import func, cast, Integer

import config
from database import SessionLocal
from schemas import IncidentReportInput, StatusUpdateRequest, ApprovalRequest
from orchestrator import run_workflow

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


def _db():
    return SessionLocal()


def _err(msg: str, code: int = 400, details: str = None) -> tuple:
    body = {"error": msg}
    if details:
        body["details"] = details
    return jsonify(body), code


# ── Health ────────────────────────────────────────────────────────────────────

@api_bp.get("/health")
def health():
    from services.gemini_service import is_available
    db = _db()
    try:
        from models.incident import Incident
        db.query(Incident).count()
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        db.close()

    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": is_available(),
        "demo_mode": config.DEMO_MODE,
        "database": "ok" if db_ok else "error",
        "model": config.GEMINI_MODEL,
    })


# ── Incidents ─────────────────────────────────────────────────────────────────

@api_bp.post("/incidents")
def create_incident():
    body = request.get_json(silent=True)
    if not body:
        return _err("Request body must be JSON")

    # Enforce max report length
    raw = body.get("raw_report", "")
    if len(raw) > config.MAX_REPORT_LENGTH:
        return _err(f"raw_report exceeds maximum length of {config.MAX_REPORT_LENGTH} characters")

    try:
        input_data = IncidentReportInput(**body)
    except ValidationError as exc:
        return _err("Validation error", 422, str(exc))

    db = _db()
    try:
        result = run_workflow(input_data, db)
        status_code = 201 if result.get("status") in ("SUCCESS", "PARTIAL") else 500
        return jsonify(result), status_code
    except Exception as exc:
        logger.error("Workflow error: %s", exc, exc_info=True)
        return _err("Internal workflow error", 500)
    finally:
        db.close()


@api_bp.get("/incidents")
def list_incidents():
    from models.incident import Incident

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(request.args.get("per_page", config.DEFAULT_PAGE_SIZE, type=int), config.MAX_PAGE_SIZE)
    severity_filter = request.args.get("severity")
    status_filter = request.args.get("status")

    db = _db()
    try:
        q = db.query(Incident)
        if severity_filter:
            q = q.filter(Incident.severity == severity_filter.upper())
        if status_filter:
            q = q.filter(Incident.status == status_filter.upper())
        total = q.count()
        incidents = (
            q.order_by(Incident.risk_score.desc().nullslast(), Incident.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "incidents": [i.to_dict() for i in incidents],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
        })
    finally:
        db.close()


@api_bp.get("/incidents/<incident_id>")
def get_incident(incident_id: str):
    from models.incident import Incident
    from models.assessment import RiskAssessment
    from models.resource import ResourceRecommendation
    from models.plan import ResponsePlan
    from models.execution import AgentExecution

    db = _db()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return _err("Incident not found", 404)

        risk = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).first()
        resources = db.query(ResourceRecommendation).filter(ResourceRecommendation.incident_id == incident_id).all()
        plan = db.query(ResponsePlan).filter(ResponsePlan.incident_id == incident_id).first()
        execs = db.query(AgentExecution).filter(AgentExecution.incident_id == incident_id).order_by(AgentExecution.created_at).all()

        return jsonify({
            "incident": inc.to_dict(),
            "risk_assessment": risk.to_dict() if risk else None,
            "resources": [r.to_dict() for r in resources],
            "response_plan": plan.to_dict() if plan else None,
            "agent_executions": [e.to_dict() for e in execs],
        })
    finally:
        db.close()


@api_bp.patch("/incidents/<incident_id>/status")
def update_status(incident_id: str):
    from models.incident import Incident
    from models.execution import IncidentEvent

    body = request.get_json(silent=True) or {}
    try:
        req = StatusUpdateRequest(**body)
    except ValidationError as exc:
        return _err("Validation error", 422, str(exc))

    db = _db()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return _err("Incident not found", 404)
        old_status = inc.status
        inc.status = req.status
        inc.updated_at = datetime.now(timezone.utc)
        db.add(IncidentEvent(
            incident_id=incident_id,
            event_type="STATUS_CHANGED",
            description=f"Status changed from {old_status} to {req.status}",
            actor=request.headers.get("X-Operator-Name", "operator"),
        ))
        db.commit()
        return jsonify({"incident_id": incident_id, "status": inc.status})
    finally:
        db.close()


@api_bp.post("/incidents/<incident_id>/approve")
def approve_incident(incident_id: str):
    from models.incident import Incident
    from models.plan import ResponsePlan
    from models.execution import IncidentEvent, OperatorApproval

    body = request.get_json(silent=True) or {}
    try:
        req = ApprovalRequest(**body)
    except ValidationError as exc:
        return _err("Validation error", 422, str(exc))

    db = _db()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return _err("Incident not found", 404)

        plan = db.query(ResponsePlan).filter(ResponsePlan.incident_id == incident_id).first()
        if not plan:
            return _err("No response plan found for this incident", 404)

        plan.approval_status = req.decision
        plan.approved_by = req.operator_name
        plan.approved_at = datetime.now(timezone.utc)

        if req.decision == "APPROVED":
            inc.status = "APPROVED"
        elif req.decision == "REJECTED":
            inc.status = "UNDER_REVIEW"

        db.add(OperatorApproval(
            incident_id=incident_id,
            plan_id=plan.id,
            operator_name=req.operator_name,
            decision=req.decision,
            notes=req.notes,
        ))
        db.add(IncidentEvent(
            incident_id=incident_id,
            event_type="PLAN_APPROVAL",
            description=f"Plan {req.decision} by {req.operator_name}. Notes: {req.notes or 'none'}",
            actor=req.operator_name,
        ))
        db.commit()
        return jsonify({
            "incident_id": incident_id,
            "plan_id": plan.id,
            "decision": req.decision,
            "approved_by": req.operator_name,
            "disclaimer": "No emergency services have been dispatched. This records the operator decision only.",
        })
    finally:
        db.close()


@api_bp.get("/incidents/<incident_id>/events")
def incident_events(incident_id: str):
    from models.execution import IncidentEvent
    db = _db()
    try:
        events = (
            db.query(IncidentEvent)
            .filter(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.created_at)
            .all()
        )
        return jsonify({"events": [e.to_dict() for e in events]})
    finally:
        db.close()


# ── Queue ─────────────────────────────────────────────────────────────────────

@api_bp.get("/queue")
def priority_queue():
    from models.incident import Incident
    db = _db()
    try:
        active = (
            db.query(Incident)
            .filter(Incident.status.notin_(["RESOLVED", "CANCELLED"]))
            .order_by(Incident.risk_score.desc().nullslast(), Incident.created_at.desc())
            .limit(50)
            .all()
        )
        return jsonify({"queue": [i.to_dict() for i in active]})
    finally:
        db.close()


# ── Resources ─────────────────────────────────────────────────────────────────

@api_bp.get("/resources")
def list_resources():
    from models.resource import ResourceInventory
    db = _db()
    try:
        items = db.query(ResourceInventory).all()
        return jsonify({
            "resources": [r.to_dict() for r in items],
            "data_provenance": "DEMO_DATA — quantities and availability are sample values for demonstration only.",
        })
    finally:
        db.close()


# ── Analytics ─────────────────────────────────────────────────────────────────

@api_bp.get("/analytics")
def analytics():
    from models.incident import Incident
    from models.execution import AgentExecution
    db = _db()
    try:
        total = db.query(Incident).count()
        by_severity = dict(
            db.query(Incident.severity, func.count(Incident.id))
            .filter(Incident.severity.isnot(None))
            .group_by(Incident.severity)
            .all()
        )
        by_status = dict(
            db.query(Incident.status, func.count(Incident.id))
            .group_by(Incident.status)
            .all()
        )
        by_type = dict(
            db.query(Incident.incident_type, func.count(Incident.id))
            .filter(Incident.incident_type.isnot(None))
            .group_by(Incident.incident_type)
            .all()
        )
        # Agent stats
        agent_stats = db.query(
            AgentExecution.agent_name,
            func.count(AgentExecution.id).label("total"),
            func.sum(cast(AgentExecution.used_fallback, Integer)).label("fallbacks"),
            func.avg(AgentExecution.duration_ms).label("avg_ms"),
        ).group_by(AgentExecution.agent_name).all()

        return jsonify({
            "total_incidents": total,
            "by_severity": by_severity,
            "by_status": by_status,
            "by_type": by_type,
            "agent_stats": [
                {
                    "agent_name": row.agent_name,
                    "total_executions": row.total,
                    "fallback_count": int(row.fallbacks or 0),
                    "avg_duration_ms": round(float(row.avg_ms or 0), 2),
                }
                for row in agent_stats
            ],
            "disclaimer": "Statistics are from the local SQLite demo database.",
        })
    finally:
        db.close()


# ── Demo reset ────────────────────────────────────────────────────────────────

@api_bp.post("/demo/reset")
def demo_reset():
    """Reset only records marked is_demo='true'. Production records are untouched."""
    from models.incident import Incident
    from models.assessment import RiskAssessment
    from models.resource import ResourceRecommendation, ResourceInventory
    from models.plan import ResponsePlan
    from models.execution import AgentExecution, IncidentEvent, OperatorApproval

    db = _db()
    try:
        demo_incidents = db.query(Incident).filter(Incident.is_demo == "true").all()
        demo_ids = [i.id for i in demo_incidents]

        for iid in demo_ids:
            db.query(OperatorApproval).filter(OperatorApproval.incident_id == iid).delete()
            db.query(IncidentEvent).filter(IncidentEvent.incident_id == iid).delete()
            db.query(AgentExecution).filter(AgentExecution.incident_id == iid).delete()
            db.query(ResponsePlan).filter(ResponsePlan.incident_id == iid).delete()
            db.query(ResourceRecommendation).filter(ResourceRecommendation.incident_id == iid).delete()
            db.query(RiskAssessment).filter(RiskAssessment.incident_id == iid).delete()

        db.query(Incident).filter(Incident.is_demo == "true").delete()
        db.commit()
        return jsonify({"reset": True, "demo_incidents_removed": len(demo_ids)})
    finally:
        db.close()
