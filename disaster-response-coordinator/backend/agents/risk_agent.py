"""
Agent 2: Risk Assessment Agent
================================
Calculates a transparent, documented risk score from 0–100 using weighted
factors derived from the incident. Score is computed entirely in Python —
not accepted from a language model.

DISCLAIMER: This scoring model is a DEMONSTRATION prototype.
It requires expert calibration before use in real emergency operations.
"""
from __future__ import annotations
import logging
from typing import Optional

from schemas import ExtractedIncident, RiskAssessmentOutput

logger = logging.getLogger(__name__)

# ── Scoring weights (sum should be ~100 for full scale) ──────────────────────
# Each factor contributes independently; weights chosen for demonstration.
# Operators should recalibrate with domain experts.
WEIGHTS = {
    "population_scale":     25,   # Number of people affected
    "injuries_present":     20,   # Confirmed injuries or medical need
    "incident_severity":    20,   # Baseline severity by disaster type
    "immediate_threats":    15,   # Active dangers flagged
    "missing_persons":      10,   # Unaccounted people
    "missing_information":  10,   # Unknown critical data = precautionary risk
}

# Baseline severity scores per incident type (0–20 scale for incident_severity weight)
INCIDENT_BASE_SEVERITY: dict[str, float] = {
    "earthquake":           20,
    "tsunami":              20,
    "cyclone":              18,
    "building_collapse":    18,
    "landslide":            16,
    "flood":                15,
    "fire":                 15,
    "industrial_accident":  14,
    "gas_leak":             13,
    "epidemic":             12,
    "other":                10,
}


def _population_score(population: Optional[int]) -> float:
    """Map reported population to a 0–25 score."""
    if population is None:
        # Unknown population is NOT low risk; apply moderate precautionary value
        return 12.0
    if population >= 500:
        return 25.0
    if population >= 200:
        return 20.0
    if population >= 100:
        return 16.0
    if population >= 50:
        return 12.0
    if population >= 20:
        return 8.0
    return 4.0


def _injury_score(injuries: Optional[int], threats: list[str]) -> float:
    """Map confirmed injuries plus medical threats to 0–20."""
    # Check for medical threats in text even without a count
    medical_threat = any("medical" in t.lower() or "elderly" in t.lower() or "child" in t.lower() or "injured" in t.lower() for t in threats)

    if injuries is None and not medical_threat:
        return 5.0   # No confirmed injuries but don't assume zero risk

    base = 0.0
    if injuries is not None:
        if injuries >= 50:
            base = 20.0
        elif injuries >= 20:
            base = 16.0
        elif injuries >= 5:
            base = 12.0
        elif injuries >= 1:
            base = 8.0

    if medical_threat and base < 8.0:
        base = 8.0
    return min(base, 20.0)


def _threats_score(threats: list[str]) -> float:
    """Map number and type of immediate threats to 0–15."""
    if not threats:
        return 0.0
    score = min(len(threats) * 4.0, 12.0)
    # Bonus for escalating / critical keywords
    critical = ["rising", "spreading", "explosion", "trapped", "collapse"]
    if any(any(c in t.lower() for c in critical) for t in threats):
        score += 3.0
    return min(score, 15.0)


def _missing_persons_score(missing: Optional[int]) -> float:
    """Map missing persons to 0–10."""
    if missing is None:
        return 2.0
    if missing >= 50:
        return 10.0
    if missing >= 10:
        return 7.0
    if missing >= 1:
        return 4.0
    return 0.0


def _missing_info_score(missing_info: list[str]) -> float:
    """
    Partial information increases precautionary risk (0–10).
    Unknown = not safe to assume low risk.
    """
    if not missing_info:
        return 0.0
    return min(len(missing_info) * 2.5, 10.0)


def compute_risk_score(incident: ExtractedIncident) -> tuple[float, list[str]]:
    """
    Compute the 0–100 risk score and return (score, contributing_factors list).
    All computation is transparent Python arithmetic.
    """
    factors: list[str] = []

    # 1. Population
    pop_s = _population_score(incident.affected_population)
    if incident.affected_population is None:
        factors.append(f"Population unknown — precautionary score applied: {pop_s:.1f}/25")
    else:
        factors.append(f"Affected population ({incident.affected_population}): {pop_s:.1f}/25")

    # 2. Injuries / medical
    inj_s = _injury_score(incident.injuries_reported, incident.immediate_threats)
    factors.append(f"Injuries/medical need score: {inj_s:.1f}/20")

    # 3. Incident type baseline
    base = INCIDENT_BASE_SEVERITY.get(incident.incident_type, 10)
    factors.append(f"Incident type '{incident.incident_type}' baseline: {base:.1f}/20")

    # 4. Immediate threats
    thr_s = _threats_score(incident.immediate_threats)
    factors.append(f"Immediate threats ({len(incident.immediate_threats)} identified): {thr_s:.1f}/15")

    # 5. Missing persons
    miss_s = _missing_persons_score(incident.missing_persons_reported)
    factors.append(f"Missing persons score: {miss_s:.1f}/10")

    # 6. Missing information (precautionary)
    info_s = _missing_info_score(incident.missing_information)
    factors.append(f"Missing information precautionary score: {info_s:.1f}/10")

    total = pop_s + inj_s + base + thr_s + miss_s + info_s
    total = round(min(total, 100.0), 2)
    return total, factors


def _score_to_severity(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _assess_confidence(incident: ExtractedIncident) -> float:
    """Lower confidence when many facts are missing."""
    base = incident.confidence
    penalty = len(incident.missing_information) * 0.05
    return max(0.15, round(base - penalty, 2))


def process(incident: ExtractedIncident) -> RiskAssessmentOutput:
    """
    Main entry point for the Risk Assessment Agent.
    Risk score is always computed deterministically in Python.
    Gemini is NOT used for score generation (avoiding opaque AI scoring).
    """
    score, factors = compute_risk_score(incident)
    severity = _score_to_severity(score)
    confidence = _assess_confidence(incident)
    requires_review = (
        confidence < 0.4
        or len(incident.missing_information) >= 3
        or incident.processing_source == "fallback"
    )

    rationale = (
        f"Risk score {score:.1f}/100 → severity {severity}. "
        f"Key drivers: {', '.join(factors[:3])}. "
        f"{'HUMAN REVIEW RECOMMENDED due to low confidence or missing data.' if requires_review else ''}"
    )

    logger.info(
        "Risk assessment: score=%.1f severity=%s confidence=%.2f requires_review=%s",
        score, severity, confidence, requires_review,
    )

    return RiskAssessmentOutput(
        risk_score=score,
        severity=severity,
        contributing_factors=factors,
        rationale=rationale,
        confidence=confidence,
        requires_human_review=requires_review,
    )
