"""
Resource service — configurable demo inventory and playbook rules.
IMPORTANT: All quantities are DEMO DATA. Availability is UNKNOWN unless
confirmed by a live external inventory system.
"""
from __future__ import annotations
from typing import List, Dict, Any

# ── Demo resource inventory ───────────────────────────────────────────────────
DEMO_INVENTORY: List[Dict[str, Any]] = [
    {
        "resource_type": "rescue_team",
        "name": "NDRF Team Alpha",
        "base_location": "NDRF Station, Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "total_quantity": 5,
        "available_quantity": 3,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "ambulance",
        "name": "GH Ambulance Pool",
        "base_location": "Government Hospital, Anna Nagar",
        "latitude": 13.0850,
        "longitude": 80.2101,
        "total_quantity": 12,
        "available_quantity": 8,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "boat",
        "name": "Coast Guard Flood Boats",
        "base_location": "Marina Beach, Chennai",
        "latitude": 13.0500,
        "longitude": 80.2824,
        "total_quantity": 10,
        "available_quantity": 6,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "fire_engine",
        "name": "Chennai Fire Station A",
        "base_location": "Egmore Fire Station",
        "latitude": 13.0750,
        "longitude": 80.2617,
        "total_quantity": 8,
        "available_quantity": 5,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "medical_personnel",
        "name": "Emergency Medical Team",
        "base_location": "Rajiv Gandhi Hospital",
        "latitude": 13.1067,
        "longitude": 80.2206,
        "total_quantity": 30,
        "available_quantity": 18,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "shelter",
        "name": "Anna Nagar Community Hall",
        "base_location": "Anna Nagar West",
        "latitude": 13.0878,
        "longitude": 80.2085,
        "total_quantity": 500,
        "available_quantity": 500,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo shelter. Capacity unverified.",
    },
    {
        "resource_type": "food_supply",
        "name": "Civil Supplies Depot",
        "base_location": "Ambattur, Chennai",
        "latitude": 13.1143,
        "longitude": 80.1548,
        "total_quantity": 1000,
        "available_quantity": 800,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
    {
        "resource_type": "water_supply",
        "name": "CMWSSB Water Tankers",
        "base_location": "CMWSSB Depot, Manali",
        "latitude": 13.1667,
        "longitude": 80.2500,
        "total_quantity": 20,
        "available_quantity": 15,
        "data_provenance": "DEMO_DATA",
        "notes": "Demo record. Availability unverified.",
    },
]

# ── Resource playbook: minimum recommended resources per incident type and severity ──
RESOURCE_PLAYBOOK: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "flood": {
        "LOW":      [{"resource_type": "rescue_team", "qty": 1}, {"resource_type": "ambulance", "qty": 2}],
        "MEDIUM":   [{"resource_type": "rescue_team", "qty": 2}, {"resource_type": "boat", "qty": 3}, {"resource_type": "ambulance", "qty": 4}, {"resource_type": "shelter", "qty": 1}],
        "HIGH":     [{"resource_type": "rescue_team", "qty": 4}, {"resource_type": "boat", "qty": 6}, {"resource_type": "ambulance", "qty": 6}, {"resource_type": "medical_personnel", "qty": 10}, {"resource_type": "shelter", "qty": 2}, {"resource_type": "water_supply", "qty": 3}],
        "CRITICAL": [{"resource_type": "rescue_team", "qty": 6}, {"resource_type": "boat", "qty": 10}, {"resource_type": "ambulance", "qty": 10}, {"resource_type": "medical_personnel", "qty": 20}, {"resource_type": "shelter", "qty": 3}, {"resource_type": "food_supply", "qty": 5}, {"resource_type": "water_supply", "qty": 5}],
    },
    "earthquake": {
        "LOW":      [{"resource_type": "rescue_team", "qty": 1}, {"resource_type": "ambulance", "qty": 2}],
        "MEDIUM":   [{"resource_type": "rescue_team", "qty": 3}, {"resource_type": "ambulance", "qty": 5}, {"resource_type": "medical_personnel", "qty": 5}],
        "HIGH":     [{"resource_type": "rescue_team", "qty": 5}, {"resource_type": "ambulance", "qty": 8}, {"resource_type": "medical_personnel", "qty": 15}, {"resource_type": "shelter", "qty": 2}],
        "CRITICAL": [{"resource_type": "rescue_team", "qty": 8}, {"resource_type": "ambulance", "qty": 12}, {"resource_type": "medical_personnel", "qty": 25}, {"resource_type": "shelter", "qty": 4}, {"resource_type": "food_supply", "qty": 6}, {"resource_type": "water_supply", "qty": 4}],
    },
    "fire": {
        "LOW":      [{"resource_type": "fire_engine", "qty": 1}, {"resource_type": "ambulance", "qty": 1}],
        "MEDIUM":   [{"resource_type": "fire_engine", "qty": 3}, {"resource_type": "ambulance", "qty": 3}, {"resource_type": "rescue_team", "qty": 1}],
        "HIGH":     [{"resource_type": "fire_engine", "qty": 5}, {"resource_type": "ambulance", "qty": 5}, {"resource_type": "rescue_team", "qty": 2}, {"resource_type": "medical_personnel", "qty": 8}],
        "CRITICAL": [{"resource_type": "fire_engine", "qty": 8}, {"resource_type": "ambulance", "qty": 8}, {"resource_type": "rescue_team", "qty": 3}, {"resource_type": "medical_personnel", "qty": 15}, {"resource_type": "shelter", "qty": 2}],
    },
    "default": {
        "LOW":      [{"resource_type": "rescue_team", "qty": 1}, {"resource_type": "ambulance", "qty": 2}],
        "MEDIUM":   [{"resource_type": "rescue_team", "qty": 2}, {"resource_type": "ambulance", "qty": 4}, {"resource_type": "medical_personnel", "qty": 5}],
        "HIGH":     [{"resource_type": "rescue_team", "qty": 4}, {"resource_type": "ambulance", "qty": 6}, {"resource_type": "medical_personnel", "qty": 10}, {"resource_type": "shelter", "qty": 1}],
        "CRITICAL": [{"resource_type": "rescue_team", "qty": 6}, {"resource_type": "ambulance", "qty": 10}, {"resource_type": "medical_personnel", "qty": 20}, {"resource_type": "shelter", "qty": 3}, {"resource_type": "food_supply", "qty": 4}, {"resource_type": "water_supply", "qty": 4}],
    },
}


def get_playbook_resources(incident_type: str, severity: str) -> List[Dict[str, Any]]:
    """Return base resource list from playbook for given incident type and severity."""
    playbook = RESOURCE_PLAYBOOK.get(incident_type, RESOURCE_PLAYBOOK["default"])
    return playbook.get(severity, playbook.get("MEDIUM", []))


def scale_for_population(resources: List[Dict], affected_population: int | None) -> List[Dict]:
    """Scale resource quantities up for large affected populations."""
    if not affected_population or affected_population < 50:
        return resources
    scale = 1.0
    if affected_population >= 500:
        scale = 2.5
    elif affected_population >= 200:
        scale = 1.8
    elif affected_population >= 100:
        scale = 1.4
    elif affected_population >= 50:
        scale = 1.2
    return [
        {**r, "recommended_quantity": max(1, round(r.get("recommended_quantity", r.get("qty", 1)) * scale))}
        for r in resources
    ]


# ── Sample locations for logistics ───────────────────────────────────────────
SAMPLE_SHELTERS = [
    {"name": "Anna Nagar Community Hall [DEMO]", "latitude": 13.0878, "longitude": 80.2085, "capacity": 500},
    {"name": "Koyambedu Shelter [DEMO]", "latitude": 13.0694, "longitude": 80.1948, "capacity": 800},
    {"name": "Adyar Relief Camp [DEMO]", "latitude": 13.0067, "longitude": 80.2575, "capacity": 300},
]

SAMPLE_HOSPITALS = [
    {"name": "Government General Hospital [DEMO]", "latitude": 13.0827, "longitude": 80.2707, "beds": 2400},
    {"name": "Rajiv Gandhi Government Hospital [DEMO]", "latitude": 13.1067, "longitude": 80.2206, "beds": 960},
    {"name": "Kilpauk Medical College [DEMO]", "latitude": 13.0850, "longitude": 80.2396, "beds": 1200},
]
