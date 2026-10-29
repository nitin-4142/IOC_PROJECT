"""
Agent 4: Logistics and Routing Agent
=======================================
Matches proposed resources to sample bases and calculates estimated routes
when valid coordinates are available.

IMPORTANT: All routes are ESTIMATES using straight-line distance with a
road factor. Road conditions are UNVERIFIED. Never present these as safe
confirmed routes for real dispatch.
"""
from __future__ import annotations
import logging
from typing import Optional

from schemas import ExtractedIncident, ResourcePlanOutput, LogisticsOutput, RouteInfo
from services import resource_service, routing_service

logger = logging.getLogger(__name__)


def _find_nearest(lat: float, lon: float, locations: list[dict]) -> Optional[dict]:
    """Return the nearest sample location by straight-line distance."""
    best = None
    best_dist = float("inf")
    for loc in locations:
        if loc.get("latitude") and loc.get("longitude"):
            d = routing_service.haversine_km(lat, lon, loc["latitude"], loc["longitude"])
            if d < best_dist:
                best_dist = d
                best = {**loc, "_distance_km": round(d, 2)}
    return best


def _build_resource_routes(
    incident_lat: float,
    incident_lon: float,
    resource_types: list[str],
    db_session=None,
) -> list[RouteInfo]:
    """Build route info from each resource base to the incident location."""
    routes: list[RouteInfo] = []
    seen_bases: set[str] = set()

    if db_session:
        try:
            from models.resource import ResourceInventory
            items = (
                db_session.query(ResourceInventory)
                .filter(ResourceInventory.resource_type.in_(resource_types))
                .all()
            )
            for item in items:
                if item.latitude and item.longitude and item.base_location not in seen_bases:
                    seen_bases.add(item.base_location or str(item.id))
                    route = routing_service.get_route(
                        item.latitude, item.longitude,
                        incident_lat, incident_lon,
                        from_label=f"{item.name or item.resource_type} [DEMO]",
                        to_label="Incident Location",
                    )
                    routes.append(RouteInfo(**route))
        except Exception as exc:
            logger.warning("Route calculation from DB failed: %s", exc)

    return routes[:5]  # Limit to 5 routes


def process(
    incident: ExtractedIncident,
    resource_plan: ResourcePlanOutput,
    db_session=None,
) -> LogisticsOutput:
    """
    Main entry point for the Logistics and Routing Agent.
    """
    lat = incident.latitude
    lon = incident.longitude
    location_available = lat is not None and lon is not None

    warnings: list[str] = []
    routes: list[RouteInfo] = []
    nearby_shelters: list[dict] = []
    nearby_hospitals: list[dict] = []

    if not location_available:
        warnings.append(
            "No verified GPS coordinates available for this incident. "
            "Routes cannot be calculated. Operators must verify location before dispatch."
        )
        if incident.location_text:
            warnings.append(
                f"Location text provided: '{incident.location_text}' — "
                "requires geocoding before routing is possible."
            )
        notes = (
            "Logistics unavailable: GPS coordinates not provided or verified. "
            "All routing requires confirmed coordinates."
        )
        return LogisticsOutput(
            location_available=False,
            routes=[],
            nearby_shelters=[],
            nearby_hospitals=[],
            warnings=warnings,
            notes=notes,
            processing_source="fallback_no_location",
        )

    # We have coordinates — calculate routes and find nearby facilities
    resource_types = [r.resource_type for r in resource_plan.resources]
    routes = _build_resource_routes(lat, lon, resource_types, db_session)

    # Find nearest shelters and hospitals from sample data
    nearest_shelter = _find_nearest(lat, lon, resource_service.SAMPLE_SHELTERS)
    nearest_hospital = _find_nearest(lat, lon, resource_service.SAMPLE_HOSPITALS)

    if nearest_shelter:
        nearby_shelters = [nearest_shelter]
    if nearest_hospital:
        nearby_hospitals = [nearest_hospital]

    warnings.extend([
        "All route distances are ESTIMATES (straight-line × 1.4 road factor). NOT verified.",
        "Road conditions, bridge safety, and accessibility are UNVERIFIED.",
        "Sample shelter/hospital locations are DEMO DATA only.",
        "DO NOT use these estimates for real operational dispatch.",
    ])

    notes = (
        f"Logistics calculated for incident at ({lat:.4f}, {lon:.4f}). "
        f"{len(routes)} resource base routes estimated. "
        "All data is DEMO — no real routing provider connected."
    )

    logger.info(
        "Logistics agent: location_available=%s, routes=%d, shelters=%d, hospitals=%d",
        location_available, len(routes), len(nearby_shelters), len(nearby_hospitals),
    )

    return LogisticsOutput(
        location_available=True,
        routes=routes,
        nearby_shelters=nearby_shelters,
        nearby_hospitals=nearby_hospitals,
        warnings=warnings,
        notes=notes,
        processing_source="sample_data+estimate",
    )
