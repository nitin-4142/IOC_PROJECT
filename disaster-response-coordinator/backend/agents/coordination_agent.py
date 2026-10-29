"""
Agent 5: Coordination and Monitoring Agent
============================================
Integrates outputs from Agents 1–4, generates a unified response plan,
detects conflicts, tracks incident status, and maintains an audit trail.

IMPORTANT: This agent generates RECOMMENDATIONS only.
No real emergency services are dispatched. Explicit human approval is
required before any action that communicates with or dispatches real services.
"""
from __future__ import annotations
import logging
from typing import Optional

from schemas import (
    ExtractedIncident,
    RiskAssessmentOutput,
    ResourcePlanOutput,
    LogisticsOutput,
    CoordinationOutput,
)

logger = logging.getLogger(__name__)

# ── Status state machine ──────────────────────────────────────────────────────
VALID_STATUSES = {
    "NEW", "UNDER_REVIEW", "AWAITING_INFORMATION",
    "PLAN_READY", "APPROVED", "IN_PROGRESS", "RESOLVED", "CANCELLED"
}


def _build_priority_actions(
    incident: ExtractedIncident,
    risk: RiskAssessmentOutput,
    resources: ResourcePlanOutput,
    logistics: LogisticsOutput,
) -> list[str]:
    """Generate an ordered list of recommended priority actions."""
    actions: list[str] = []

    # 1. Life safety first
    if risk.severity in ("CRITICAL", "HIGH"):
        actions.append(
            f"[IMMEDIATE] Deploy rescue teams to {incident.location_text or 'reported location'} "
            f"for life-safety operations — {incident.affected_population or 'unknown'} people reported affected."
        )
    else:
        actions.append(
            f"[URGENT] Dispatch assessment team to {incident.location_text or 'reported location'}."
        )

    # 2. Medical
    needs_medical = any(
        "medical" in t.lower() or "elderly" in t.lower() or "injured" in t.lower()
        for t in incident.immediate_threats
    )
    if needs_medical or (incident.injuries_reported and incident.injuries_reported > 0):
        actions.append(
            "[MEDICAL] Mobilise ambulances and medical personnel for triage and treatment."
        )

    # 3. Flood-specific
    if incident.incident_type == "flood":
        actions.append("[RESCUE] Deploy flood rescue boats for rooftop/waterlogged area evacuations.")

    # 4. Shelter
    shelter_rec = next(
        (r for r in resources.resources if r.resource_type == "shelter"), None
    )
    if shelter_rec and logistics.nearby_shelters:
        shelter = logistics.nearby_shelters[0]
        actions.append(
            f"[SHELTER] Activate {shelter.get('name', 'nearby shelter')} for displaced persons. "
            "[DEMO DATA — verify availability before announcement]"
        )

    # 5. Situational awareness
    actions.append(
        "[COMMS] Establish communication with local civil administration and confirm actual resource availability."
    )

    # 6. Human review if needed
    if risk.requires_human_review:
        actions.append(
            "[REVIEW] Human operator review required before escalating response — "
            "assessment confidence is below threshold or data is incomplete."
        )

    return actions


def _detect_conflicts(resources: ResourcePlanOutput, db_session=None) -> list[str]:
    """Identify potential resource conflicts in the demo inventory."""
    conflicts: list[str] = []
    if db_session:
        try:
            from models.resource import ResourceInventory
            for rec in resources.resources:
                inv = (
                    db_session.query(ResourceInventory)
                    .filter(ResourceInventory.resource_type == rec.resource_type)
                    .first()
                )
                if inv and inv.available_quantity < rec.recommended_quantity:
                    conflicts.append(
                        f"[DEMO] {rec.resource_type}: recommended {rec.recommended_quantity}, "
                        f"demo-available {inv.available_quantity} — potential shortfall."
                    )
        except Exception as exc:
            logger.warning("Conflict detection failed: %s", exc)
    return conflicts


def _build_missing_flags(
    incident: ExtractedIncident,
    risk: RiskAssessmentOutput,
    logistics: LogisticsOutput,
) -> list[str]:
    """Collect all flags about missing or uncertain data."""
    flags = list(incident.missing_information)
    if not logistics.location_available:
        flags.append("GPS coordinates unavailable — routing and logistics incomplete.")
    if risk.requires_human_review:
        flags.append("Risk assessment confidence is low — human validation recommended.")
    if incident.processing_source == "fallback":
        flags.append("Incident analysis used rule-based fallback (Gemini unavailable) — verify classification.")
    return flags


def _follow_up_questions(
    incident: ExtractedIncident,
    missing_flags: list[str],
) -> list[str]:
    """Generate follow-up questions for operators."""
    questions: list[str] = []
    if incident.affected_population is None:
        questions.append("How many people are currently affected or displaced?")
    if not incident.latitude:
        questions.append("Can you provide GPS coordinates or a precise address for the incident?")
    if incident.incident_type == "flood":
        questions.append("What is the current water level and is it still rising?")
    if incident.injuries_reported is None:
        questions.append("Are there any confirmed injuries or fatalities?")
    if incident.incident_type in ("building_collapse", "earthquake"):
        questions.append("How many floors are involved and are people confirmed trapped?")
    if len(questions) == 0:
        questions.append("Please confirm the current on-site situation and update every 30 minutes.")
    return questions


def _build_summary(
    incident: ExtractedIncident,
    risk: RiskAssessmentOutput,
    resources: ResourcePlanOutput,
    logistics: LogisticsOutput,
) -> str:
    loc = incident.location_text or "location unspecified"
    pop = f"{incident.affected_population} people" if incident.affected_population else "unknown number of people"
    route_note = (
        f"{len(logistics.routes)} resource route(s) estimated (DEMO)"
        if logistics.location_available
        else "routing unavailable (no GPS coordinates)"
    )
    return (
        f"{incident.incident_type.upper()} incident at {loc}. "
        f"Approximately {pop} reported affected. "
        f"Risk: {risk.severity} (score {risk.risk_score:.0f}/100). "
        f"{len(resources.resources)} resource type(s) recommended. "
        f"{route_note}. "
        f"Status: PLAN READY — awaiting operator review and approval. "
        f"NOTE: This is a RECOMMENDATION. No services have been dispatched."
    )


def process(
    incident: ExtractedIncident,
    risk: RiskAssessmentOutput,
    resources: ResourcePlanOutput,
    logistics: LogisticsOutput,
    db_session=None,
) -> CoordinationOutput:
    """
    Main entry point for the Coordination and Monitoring Agent.
    """
    priority_actions = _build_priority_actions(incident, risk, resources, logistics)
    conflicts = _detect_conflicts(resources, db_session)
    missing_flags = _build_missing_flags(incident, risk, logistics)
    follow_up = _follow_up_questions(incident, missing_flags)
    summary = _build_summary(incident, risk, resources, logistics)

    logistics_notes = logistics.notes
    if logistics.warnings:
        logistics_notes += "\nWARNINGS: " + "; ".join(logistics.warnings[:2])

    incident_status = "PLAN_READY"
    if missing_flags and len(missing_flags) >= 3:
        incident_status = "AWAITING_INFORMATION"

    logger.info(
        "Coordination agent: status=%s, actions=%d, conflicts=%d, flags=%d",
        incident_status, len(priority_actions), len(conflicts), len(missing_flags),
    )

    return CoordinationOutput(
        summary=summary,
        priority_actions=priority_actions,
        logistics_notes=logistics_notes,
        resource_conflicts=conflicts,
        missing_data_flags=missing_flags,
        follow_up_questions=follow_up,
        incident_status=incident_status,
    )
