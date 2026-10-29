"""
Agent 3: Resource Planning Agent
===================================
Recommends resources based on the incident type, severity, and affected
population using a configurable playbook.

IMPORTANT: All availability information is DEMO DATA unless a live inventory
system is integrated. Resources are RECOMMENDED, not confirmed as available.
"""
from __future__ import annotations
import logging

from schemas import ExtractedIncident, RiskAssessmentOutput, ResourceItem, ResourcePlanOutput
from services import resource_service

logger = logging.getLogger(__name__)

_RESOURCE_REASONS: dict[str, str] = {
    "rescue_team":         "Trained rescue personnel for search and evacuation operations",
    "ambulance":           "Medical transport for injured and vulnerable persons",
    "boat":                "Water-based rescue for flood-affected areas",
    "fire_engine":         "Firefighting and rescue capability",
    "medical_personnel":   "On-site medical assessment and treatment",
    "shelter":             "Temporary accommodation for displaced persons",
    "food_supply":         "Emergency rations for displaced/stranded persons",
    "water_supply":        "Potable water for drinking and sanitation",
}


def _get_availability(resource_type: str, db_session=None) -> tuple[str, str]:
    """
    Check demo inventory for a resource type.
    Returns (availability_status, source_description).
    Always labelled as DEMO_DATA.
    """
    if db_session is None:
        return "UNKNOWN", "No inventory system connected"

    try:
        from models.resource import ResourceInventory
        item = (
            db_session.query(ResourceInventory)
            .filter(ResourceInventory.resource_type == resource_type)
            .first()
        )
        if item:
            qty = item.available_quantity
            if qty > 0:
                status = "DEMO_AVAILABLE"
            else:
                status = "DEMO_DEPLETED"
            return status, f"DEMO_DATA from sample inventory — {item.name or resource_type} at {item.base_location or 'unknown base'}"
    except Exception as exc:
        logger.warning("Inventory lookup failed: %s", exc)

    return "UNKNOWN", "Inventory lookup failed"


def process(
    incident: ExtractedIncident,
    risk: RiskAssessmentOutput,
    db_session=None,
) -> ResourcePlanOutput:
    """
    Main entry point for the Resource Planning Agent.
    """
    incident_type = incident.incident_type
    severity = risk.severity

    # Get base resources from playbook
    base_resources = resource_service.get_playbook_resources(incident_type, severity)

    # Scale for population
    scaled = resource_service.scale_for_population(base_resources, incident.affected_population)

    # Add boats explicitly for floods if not already included
    if incident_type == "flood":
        has_boat = any(r.get("resource_type", r.get("resource_type")) == "boat" for r in scaled)
        if not has_boat:
            scaled.append({"resource_type": "boat", "recommended_quantity": 2})

    # Build ResourceItem objects with availability checks
    items: list[ResourceItem] = []
    for r in scaled:
        rtype = r.get("resource_type", "unknown")
        qty = r.get("recommended_quantity", r.get("qty", 1))
        avail, source = _get_availability(rtype, db_session)

        items.append(ResourceItem(
            resource_type=rtype,
            recommended_quantity=qty,
            reason=_RESOURCE_REASONS.get(rtype, f"Required for {incident_type} response"),
            availability_status=avail,
            source_of_availability_data=source,
        ))

    notes = (
        f"Resources recommended for {incident_type.upper()} incident at {severity} severity. "
        f"Quantities scaled for reported population of "
        f"{incident.affected_population if incident.affected_population else 'unknown'}. "
        "ALL availability data is DEMO DATA — verify with actual dispatch systems before any real deployment."
    )

    logger.info(
        "Resource agent: %d resource types recommended for %s/%s",
        len(items), incident_type, severity,
    )

    return ResourcePlanOutput(
        resources=items,
        notes=notes,
        processing_source="playbook+inventory",
    )
