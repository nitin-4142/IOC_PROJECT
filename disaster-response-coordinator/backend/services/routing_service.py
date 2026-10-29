"""
Routing service — clean interface for optional routing provider integration.
Without a real routing API, returns ROUTE_UNAVAILABLE honestly.
"""
from __future__ import annotations
import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

ROUTING_PROVIDER = "none"  # Extend to "osrm" or "google" when available


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in kilometres between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    from_label: str = "Resource Base",
    to_label: str = "Incident Location",
) -> dict:
    """
    Attempt to get a route. Returns a route dict.
    Currently returns straight-line estimate flagged as ESTIMATE_ONLY.
    """
    if ROUTING_PROVIDER == "none":
        dist = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)
        # Rough road-factor estimate: 1.4× straight line
        road_dist = round(dist * 1.4, 2)
        # Assume average urban speed ~25 km/h
        travel_min = round((road_dist / 25) * 60, 1)
        return {
            "from_location": from_label,
            "to_location": to_label,
            "estimated_distance_km": road_dist,
            "estimated_time_min": travel_min,
            "route_status": "ESTIMATE_ONLY",
            "notes": (
                "Straight-line distance multiplied by road factor 1.4. "
                "No routing provider configured. Road conditions unverified. "
                "DO NOT use for operational dispatch."
            ),
        }
    # Future: integrate OSRM or Google Maps Directions API here.
    return {
        "from_location": from_label,
        "to_location": to_label,
        "estimated_distance_km": None,
        "estimated_time_min": None,
        "route_status": "ROUTE_UNAVAILABLE",
        "notes": "Routing provider not configured.",
    }
