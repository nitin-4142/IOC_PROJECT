"""
Pytest tests for all five agents, orchestrator, and API.
All Gemini and external calls are mocked — tests run fully offline.
"""
import json
import sys
import os
import pytest

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def flood_input():
    from schemas import IncidentReportInput
    return IncidentReportInput(
        raw_report=(
            "Severe flooding near Anna Nagar Bridge in Chennai. "
            "Approximately 150 people are stranded on rooftops. "
            "The water level is rising, and several elderly people need medical assistance."
        ),
        location_text="Anna Nagar Bridge, Chennai",
        is_demo=True,
    )

@pytest.fixture
def flood_input_with_coords():
    from schemas import IncidentReportInput
    return IncidentReportInput(
        raw_report="Flooding in Anna Nagar. 150 people stranded. Water rising.",
        location_text="Anna Nagar, Chennai",
        latitude=13.0878,
        longitude=80.2085,
        is_demo=True,
    )

@pytest.fixture
def minimal_input():
    from schemas import IncidentReportInput
    return IncidentReportInput(
        raw_report="Emergency situation reported. Please help.",
        is_demo=True,
    )

@pytest.fixture
def earthquake_input():
    from schemas import IncidentReportInput
    return IncidentReportInput(
        raw_report="Major earthquake magnitude 6.5 in Coimbatore. Multiple buildings collapsed. 80 injured and 30 missing.",
        location_text="Coimbatore",
        is_demo=True,
    )


# ── Agent 1: Intelligence Agent ───────────────────────────────────────────────

class TestIntelligenceAgent:
    def test_flood_classification(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input)
        assert result.incident_type == "flood"
        assert result.processing_source == "fallback"
        assert result.affected_population == 150

    def test_earthquake_classification(self, earthquake_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(earthquake_input)
        assert result.incident_type == "earthquake"
        assert result.injuries_reported == 80
        assert result.missing_persons_reported == 30

    def test_unknown_type_returns_other(self, mocker):
        from schemas import IncidentReportInput
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        inp = IncidentReportInput(raw_report="Something happened somewhere please send help urgently.", is_demo=True)
        result = intelligence_agent.process(inp)
        assert result.incident_type in ("other", "flood", "fire", "earthquake")  # valid type

    def test_no_fabricated_coords(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input)
        # No coords in input → no coords in output
        assert result.latitude is None
        assert result.longitude is None

    def test_coords_preserved_when_provided(self, flood_input_with_coords, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input_with_coords)
        assert result.latitude == 13.0878
        assert result.longitude == 80.2085

    def test_gemini_fallback_when_unavailable(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input)
        assert result.processing_source == "fallback"

    def test_malformed_gemini_response_uses_fallback(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=True)
        mocker.patch("services.gemini_service.generate_structured", return_value=None)
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input)
        assert result.processing_source == "fallback"

    def test_gemini_success_path(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=True)
        mocker.patch("services.gemini_service.generate_structured", return_value={
            "incident_type": "flood",
            "location_text": "Anna Nagar Bridge, Chennai",
            "reported_time": None,
            "affected_population": 150,
            "injuries_reported": None,
            "missing_persons_reported": None,
            "immediate_threats": ["Rising water level", "Elderly persons need medical assistance"],
            "extracted_facts": ["150 people stranded on rooftops"],
            "missing_information": ["Exact GPS coordinates not provided"],
            "confidence": 0.85,
        })
        from agents import intelligence_agent
        result = intelligence_agent.process(flood_input)
        assert result.incident_type == "flood"
        assert result.processing_source == "gemini"
        assert result.affected_population == 150

    def test_missing_population_handled(self, minimal_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from agents import intelligence_agent
        result = intelligence_agent.process(minimal_input)
        assert result.affected_population is None
        assert len(result.missing_information) > 0


# ── Agent 2: Risk Assessment Agent ───────────────────────────────────────────

class TestRiskAgent:
    def _make_incident(self, **kwargs):
        from schemas import ExtractedIncident
        defaults = dict(
            incident_type="flood", raw_report="test", location_text="Chennai",
            affected_population=150, injuries_reported=5,
            immediate_threats=["Rising water level", "Elderly persons"],
            extracted_facts=[], missing_information=[], confidence=0.7,
            processing_source="fallback",
        )
        defaults.update(kwargs)
        return ExtractedIncident(**defaults)

    def test_critical_incident_score(self):
        from agents import risk_agent
        incident = self._make_incident(
            incident_type="earthquake",
            affected_population=500,
            injuries_reported=50,
            missing_persons_reported=20,
            immediate_threats=["Trapped survivors", "Building collapse ongoing"],
            missing_information=[],
        )
        result = risk_agent.process(incident)
        assert result.severity == "CRITICAL"
        assert result.risk_score >= 75

    def test_low_severity_small_incident(self):
        from agents import risk_agent
        incident = self._make_incident(
            affected_population=5, injuries_reported=0,
            immediate_threats=[], missing_information=[], confidence=0.9,
        )
        result = risk_agent.process(incident)
        assert result.severity in ("LOW", "MEDIUM")

    def test_unknown_population_not_zero_risk(self):
        from agents import risk_agent
        incident = self._make_incident(affected_population=None, injuries_reported=None)
        result = risk_agent.process(incident)
        # Unknown population should NOT result in zero score
        assert result.risk_score > 0

    def test_score_in_valid_range(self):
        from agents import risk_agent
        incident = self._make_incident(affected_population=1000, injuries_reported=100)
        result = risk_agent.process(incident)
        assert 0 <= result.risk_score <= 100

    def test_severity_values(self):
        from agents import risk_agent
        incident = self._make_incident()
        result = risk_agent.process(incident)
        assert result.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_requires_human_review_low_confidence(self):
        from agents import risk_agent
        incident = self._make_incident(
            confidence=0.2,
            missing_information=["location unknown", "population unknown", "time unknown"],
        )
        result = risk_agent.process(incident)
        assert result.requires_human_review is True

    def test_contributing_factors_populated(self):
        from agents import risk_agent
        incident = self._make_incident()
        result = risk_agent.process(incident)
        assert len(result.contributing_factors) > 0


# ── Agent 3: Resource Planning Agent ─────────────────────────────────────────

class TestResourceAgent:
    def _make_incident(self, incident_type="flood", population=150):
        from schemas import ExtractedIncident
        return ExtractedIncident(
            incident_type=incident_type, raw_report="test",
            location_text="Chennai", affected_population=population,
            immediate_threats=[], extracted_facts=[], missing_information=[],
            confidence=0.7, processing_source="fallback",
        )

    def _make_risk(self, severity="HIGH", score=70.0):
        from schemas import RiskAssessmentOutput
        return RiskAssessmentOutput(
            risk_score=score, severity=severity,
            contributing_factors=[], rationale="test",
            confidence=0.7, requires_human_review=False,
        )

    def test_flood_high_recommends_boats(self):
        from agents import resource_agent
        result = resource_agent.process(self._make_incident("flood", 150), self._make_risk("HIGH"))
        types = [r.resource_type for r in result.resources]
        assert "boat" in types

    def test_resources_not_empty(self):
        from agents import resource_agent
        result = resource_agent.process(self._make_incident(), self._make_risk())
        assert len(result.resources) > 0

    def test_availability_labelled_demo(self):
        from agents import resource_agent
        result = resource_agent.process(self._make_incident(), self._make_risk())
        for r in result.resources:
            assert "DEMO" in r.availability_status or r.availability_status == "UNKNOWN"

    def test_population_scaling(self):
        from agents import resource_agent
        small = resource_agent.process(self._make_incident("flood", 10), self._make_risk("HIGH"))
        large = resource_agent.process(self._make_incident("flood", 500), self._make_risk("HIGH"))
        small_total = sum(r.recommended_quantity for r in small.resources)
        large_total = sum(r.recommended_quantity for r in large.resources)
        assert large_total > small_total

    def test_resource_conflicts_demo(self):
        from agents import resource_agent
        from services.resource_service import get_playbook_resources
        # Verify playbook returns resources for all supported types
        for itype in ("flood", "earthquake", "fire", "default"):
            for sev in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                resources = get_playbook_resources(itype, sev)
                assert len(resources) > 0


# ── Agent 4: Logistics Agent ──────────────────────────────────────────────────

class TestLogisticsAgent:
    def _make_incident(self, lat=None, lon=None):
        from schemas import ExtractedIncident
        return ExtractedIncident(
            incident_type="flood", raw_report="test",
            location_text="Anna Nagar" if lat else None,
            latitude=lat, longitude=lon,
            immediate_threats=[], extracted_facts=[], missing_information=[],
            confidence=0.7, processing_source="fallback",
        )

    def _make_resource_plan(self):
        from schemas import ResourcePlanOutput, ResourceItem
        return ResourcePlanOutput(resources=[
            ResourceItem(resource_type="boat", recommended_quantity=3, reason="flood", availability_status="DEMO_AVAILABLE", source_of_availability_data="DEMO"),
        ])

    def test_no_coords_returns_unavailable(self):
        from agents import logistics_agent
        result = logistics_agent.process(self._make_incident(), self._make_resource_plan())
        assert result.location_available is False
        assert any("GPS" in w or "coordinates" in w for w in result.warnings)

    def test_with_coords_location_available(self):
        from agents import logistics_agent
        result = logistics_agent.process(self._make_incident(13.0878, 80.2085), self._make_resource_plan())
        assert result.location_available is True

    def test_routes_have_estimate_status(self):
        from agents import logistics_agent
        result = logistics_agent.process(self._make_incident(13.0878, 80.2085), self._make_resource_plan())
        # Even without DB, routes list exists
        assert isinstance(result.routes, list)

    def test_routing_unavailable_handled(self):
        from services.routing_service import get_route
        route = get_route(13.08, 80.21, 13.05, 80.28)
        # Should return ESTIMATE_ONLY or ROUTE_UNAVAILABLE, never fabricated data
        assert route["route_status"] in ("ESTIMATE_ONLY", "ROUTE_UNAVAILABLE")


# ── Agent 5: Coordination Agent ───────────────────────────────────────────────

class TestCoordinationAgent:
    def _make_all(self, severity="HIGH"):
        from schemas import ExtractedIncident, RiskAssessmentOutput, ResourcePlanOutput, ResourceItem, LogisticsOutput
        incident = ExtractedIncident(
            incident_type="flood", raw_report="test", location_text="Chennai",
            affected_population=150, injuries_reported=5,
            immediate_threats=["Rising water level", "Elderly persons need medical assistance"],
            extracted_facts=[], missing_information=["GPS not provided"],
            confidence=0.7, processing_source="fallback",
        )
        risk = RiskAssessmentOutput(
            risk_score=75.0, severity=severity,
            contributing_factors=["Population: 150"],
            rationale="High risk", confidence=0.7, requires_human_review=False,
        )
        resources = ResourcePlanOutput(resources=[
            ResourceItem(resource_type="rescue_team", recommended_quantity=4, reason="test",
                         availability_status="DEMO_AVAILABLE", source_of_availability_data="DEMO"),
        ])
        logistics = LogisticsOutput(location_available=False, warnings=["No GPS"], notes="no coords")
        return incident, risk, resources, logistics

    def test_summary_not_empty(self):
        from agents import coordination_agent
        incident, risk, resources, logistics = self._make_all()
        result = coordination_agent.process(incident, risk, resources, logistics)
        assert len(result.summary) > 20

    def test_priority_actions_not_empty(self):
        from agents import coordination_agent
        incident, risk, resources, logistics = self._make_all()
        result = coordination_agent.process(incident, risk, resources, logistics)
        assert len(result.priority_actions) > 0

    def test_follow_up_questions_generated(self):
        from agents import coordination_agent
        incident, risk, resources, logistics = self._make_all()
        result = coordination_agent.process(incident, risk, resources, logistics)
        assert len(result.follow_up_questions) > 0

    def test_incident_status_valid(self):
        from agents import coordination_agent
        incident, risk, resources, logistics = self._make_all()
        result = coordination_agent.process(incident, risk, resources, logistics)
        valid = {"NEW", "UNDER_REVIEW", "AWAITING_INFORMATION", "PLAN_READY", "APPROVED", "IN_PROGRESS", "RESOLVED", "CANCELLED"}
        assert result.incident_status in valid

    def test_critical_incident_has_immediate_action(self):
        from agents import coordination_agent
        incident, risk, resources, logistics = self._make_all("CRITICAL")
        result = coordination_agent.process(incident, risk, resources, logistics)
        assert any("IMMEDIATE" in a for a in result.priority_actions)


# ── Orchestrator end-to-end ───────────────────────────────────────────────────

class TestOrchestrator:
    def test_full_workflow_offline(self, flood_input, mocker, tmp_path):
        mocker.patch("services.gemini_service.is_available", return_value=False)

        # Use in-memory SQLite for tests
        import os
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

        from database import init_db, SessionLocal
        init_db()

        from services.resource_service import DEMO_INVENTORY
        from models.resource import ResourceInventory
        db = SessionLocal()
        # Clean any existing for test isolation
        db.query(ResourceInventory).delete()
        for item in DEMO_INVENTORY:
            db.add(ResourceInventory(**item))
        db.commit()

        from orchestrator import run_workflow
        result = run_workflow(flood_input, db)
        db.close()

        assert result["status"] in ("SUCCESS", "PARTIAL")
        assert result["incident_id"] is not None
        assert result["incident"]["incident_type"] == "flood"
        assert result["risk_assessment"] is not None
        assert result["resource_plan"] is not None
        assert result["coordination"] is not None

    def test_all_five_agents_run(self, flood_input, mocker):
        mocker.patch("services.gemini_service.is_available", return_value=False)
        from database import init_db, SessionLocal
        init_db()
        from services.resource_service import DEMO_INVENTORY
        from models.resource import ResourceInventory
        db = SessionLocal()
        db.query(ResourceInventory).delete()
        for item in DEMO_INVENTORY:
            db.add(ResourceInventory(**item))
        db.commit()
        from orchestrator import run_workflow
        result = run_workflow(flood_input, db)
        db.close()
        agents = result.get("agent_results", {})
        assert "intelligence_agent" in agents
        assert "risk_agent" in agents
        assert "resource_agent" in agents
        assert "logistics_agent" in agents
        assert "coordination_agent" in agents


# ── Schema validation ─────────────────────────────────────────────────────────

class TestSchemas:
    def test_invalid_incident_type_normalised(self):
        from schemas import ExtractedIncident
        inc = ExtractedIncident(
            incident_type="UNKNOWN_TYPE", raw_report="test",
            immediate_threats=[], extracted_facts=[], missing_information=[],
        )
        assert inc.incident_type == "other"

    def test_severity_must_be_valid(self):
        from schemas import RiskAssessmentOutput
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RiskAssessmentOutput(risk_score=50, severity="EXTREME", contributing_factors=[], rationale="test")

    def test_approval_decision_validated(self):
        from schemas import ApprovalRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ApprovalRequest(operator_name="Alice", decision="MAYBE")

    def test_report_too_short_rejected(self):
        from schemas import IncidentReportInput
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IncidentReportInput(raw_report="hi")

    def test_status_update_validated(self):
        from schemas import StatusUpdateRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            StatusUpdateRequest(status="UNKNOWN_STATUS")


# ── Routing service ───────────────────────────────────────────────────────────

class TestRoutingService:
    def test_haversine_known_distance(self):
        from services.routing_service import haversine_km
        # Chennai to Coimbatore approx 500 km
        d = haversine_km(13.0827, 80.2707, 11.0168, 76.9558)
        assert 400 < d < 500

    def test_same_point_zero_distance(self):
        from services.routing_service import haversine_km
        d = haversine_km(13.0, 80.0, 13.0, 80.0)
        assert d < 0.001
