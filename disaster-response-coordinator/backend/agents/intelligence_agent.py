"""
Agent 1: Emergency Intelligence Agent
======================================
Receives an unstructured emergency report and extracts structured incident
information using Gemini when available, or deterministic rules as fallback.

IMPORTANT: This agent NEVER fabricates GPS coordinates, casualty counts,
timestamps, or other facts not present in the input text.
"""
from __future__ import annotations
import logging
import re
from typing import Optional

from schemas import ExtractedIncident, IncidentReportInput
from services import gemini_service

logger = logging.getLogger(__name__)

# ── Keyword maps for fallback classification ──────────────────────────────────
_TYPE_KEYWORDS: dict[str, list[str]] = {
    "flood":             ["flood", "flooding", "inundated", "waterlogged", "submerged", "water level", "stranded on rooftop", "rooftop"],
    "earthquake":        ["earthquake", "tremor", "seismic", "magnitude", "richter", "aftershock", "quake"],
    "fire":              ["fire", "blaze", "burning", "flame", "smoke", "inferno", "arson"],
    "cyclone":           ["cyclone", "hurricane", "typhoon", "storm", "gale", "wind speed"],
    "landslide":         ["landslide", "mudslide", "rockfall", "hill collapse", "slope failure"],
    "building_collapse": ["building collapse", "structure collapse", "wall collapse", "collapsed building", "rubble", "debris"],
    "gas_leak":          ["gas leak", "gas pipe", "chemical leak", "toxic gas", "lpg", "png leak"],
    "industrial_accident": ["industrial accident", "factory explosion", "plant fire", "chemical spill", "explosion at"],
    "tsunami":           ["tsunami", "tidal wave"],
    "epidemic":          ["outbreak", "epidemic", "disease spread", "infection", "contamination"],
}

_POPULATION_PATTERN = re.compile(
    r"(\d+(?:,\d+)?)\s*(?:people|persons?|individuals?|residents?|victims?|survivors?|stranded)",
    re.IGNORECASE,
)
_INJURY_PATTERN = re.compile(
    r"(\d+)\s*(?:injured|injuries|wounded|hurt)",
    re.IGNORECASE,
)
_MISSING_PATTERN = re.compile(
    r"(\d+)\s*(?:missing|unaccounted)",
    re.IGNORECASE,
)

_THREAT_KEYWORDS = [
    ("rising water level", "Rising water level — escalating flood risk"),
    ("water level rising", "Rising water level — escalating flood risk"),
    ("fire spreading", "Fire spreading — immediate evacuation required"),
    ("gas leak", "Potential gas explosion hazard"),
    ("elderly", "Elderly persons present — medical vulnerability"),
    ("children", "Children present — heightened vulnerability"),
    ("injured", "Reported injuries — medical assistance required"),
    ("trapped", "People reported trapped"),
    ("missing", "Missing persons reported"),
    ("no electricity", "Power outage reported"),
    ("power cut", "Power outage reported"),
    ("bridge", "Infrastructure (bridge) potentially affected"),
]


def _classify_fallback(text: str) -> str:
    text_lower = text.lower()
    for incident_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return incident_type
    return "other"


def _extract_population_fallback(text: str) -> Optional[int]:
    matches = _POPULATION_PATTERN.findall(text)
    if matches:
        return int(matches[0].replace(",", ""))
    return None


def _extract_threats_fallback(text: str) -> list[str]:
    text_lower = text.lower()
    return [msg for kw, msg in _THREAT_KEYWORDS if kw in text_lower]


def _extract_missing_info(incident_type: str, text: str, population: Optional[int]) -> list[str]:
    missing = []
    text_lower = text.lower()
    if not any(w in text_lower for w in ["anna nagar", "street", "road", "near", "at ", "district", "city", "town", "bridge", "village"]):
        missing.append("Precise location / GPS coordinates not provided")
    if population is None:
        missing.append("Exact number of affected people unknown")
    if incident_type == "flood" and "water level" not in text_lower:
        missing.append("Current water level not specified")
    if incident_type in ("earthquake", "building_collapse") and not any(w in text_lower for w in ["magnitude", "floors", "building"]):
        missing.append("Structural damage details not provided")
    return missing


# ── Gemini prompt ────────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTION = """You are an emergency intelligence analyst. Extract structured facts from
disaster reports strictly based on what the text says. Never invent GPS coordinates, casualty numbers,
or times not mentioned in the text. Return ONLY valid JSON matching this schema:
{
  "incident_type": "<flood|earthquake|fire|cyclone|landslide|building_collapse|gas_leak|industrial_accident|tsunami|epidemic|other>",
  "location_text": "<exact location string or null>",
  "reported_time": "<time string or null>",
  "affected_population": <integer or null>,
  "injuries_reported": <integer or null>,
  "missing_persons_reported": <integer or null>,
  "immediate_threats": ["<threat description>"],
  "extracted_facts": ["<fact from text>"],
  "missing_information": ["<what is unknown>"],
  "confidence": <0.0 to 1.0>
}"""


def _build_prompt(report: str) -> str:
    return f"""Analyse this emergency report and extract structured information.

EMERGENCY REPORT:
{report}

Return ONLY a JSON object. Do not fabricate any data not in the report."""


# ── Public interface ──────────────────────────────────────────────────────────

def process(input_data: IncidentReportInput) -> ExtractedIncident:
    """
    Main entry point for the Intelligence Agent.
    Tries Gemini first; falls back to deterministic rule extraction.
    """
    report = input_data.raw_report.strip()

    # Attempt Gemini
    if gemini_service.is_available():
        try:
            result = gemini_service.generate_structured(
                prompt=_build_prompt(report),
                system_instruction=_SYSTEM_INSTRUCTION,
            )
            if result:
                incident = _parse_gemini_result(result, report, input_data)
                logger.info("Intelligence agent used Gemini for incident analysis.")
                return incident
        except Exception as exc:
            logger.warning("Intelligence agent Gemini call failed: %s", exc)

    # Deterministic fallback
    return _fallback_extraction(report, input_data)


def _parse_gemini_result(result: dict, report: str, input_data: IncidentReportInput) -> ExtractedIncident:
    """Validate and build ExtractedIncident from Gemini output."""
    population = result.get("affected_population")
    if isinstance(population, str):
        try:
            population = int(population)
        except (ValueError, TypeError):
            population = None

    return ExtractedIncident(
        incident_type=result.get("incident_type", "other"),
        raw_report=report,
        location_text=input_data.location_text or result.get("location_text"),
        latitude=input_data.latitude,   # Only use operator-supplied coords
        longitude=input_data.longitude,
        reported_time=result.get("reported_time"),
        affected_population=population,
        injuries_reported=result.get("injuries_reported"),
        missing_persons_reported=result.get("missing_persons_reported"),
        immediate_threats=result.get("immediate_threats", []),
        extracted_facts=result.get("extracted_facts", []),
        missing_information=result.get("missing_information", []),
        confidence=float(result.get("confidence", 0.7)),
        processing_source="gemini",
    )


def _fallback_extraction(report: str, input_data: IncidentReportInput) -> ExtractedIncident:
    """Rule-based incident extraction when Gemini is unavailable."""
    incident_type = _classify_fallback(report)
    population = _extract_population_fallback(report)
    injuries = None
    missing = None

    inj_matches = _INJURY_PATTERN.findall(report)
    if inj_matches:
        injuries = int(inj_matches[0])

    miss_matches = _MISSING_PATTERN.findall(report)
    if miss_matches:
        missing = int(miss_matches[0])

    threats = _extract_threats_fallback(report)
    facts = [f"Incident classified as: {incident_type}"]
    if population:
        facts.append(f"Reported affected population: {population}")
    if injuries:
        facts.append(f"Reported injuries: {injuries}")

    missing_info = _extract_missing_info(incident_type, report, population)

    return ExtractedIncident(
        incident_type=incident_type,
        raw_report=report,
        location_text=input_data.location_text or _extract_location_hint(report),
        latitude=input_data.latitude,
        longitude=input_data.longitude,
        reported_time=None,
        affected_population=population,
        injuries_reported=injuries,
        missing_persons_reported=missing,
        immediate_threats=threats,
        extracted_facts=facts,
        missing_information=missing_info,
        confidence=0.55,
        processing_source="fallback",
    )


def _extract_location_hint(text: str) -> Optional[str]:
    """Extract a rough location string from free text."""
    # Look for "near X", "at X", "in X" patterns
    patterns = [
        r"near\s+([A-Z][A-Za-z\s,]+?)(?:\.|,|\bin\b|$)",
        r"at\s+([A-Z][A-Za-z\s,]+?)(?:\.|,|\bin\b|$)",
        r"in\s+([A-Z][A-Za-z\s,]+?)(?:\.|,|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None
