"""
Pytest suite for Flask REST API endpoints, operator approval workflow,
and database reload persistence.
"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import init_db, SessionLocal
from models.incident import Incident
from models.plan import ResponsePlan


@pytest.fixture
def client():
    # Configure test database
    os.environ["DATABASE_URL"] = "sqlite:///test_disaster.db"
    init_db()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client

    # Cleanup test DB file
    if os.path.exists("test_disaster.db"):
        try:
            os.remove("test_disaster.db")
        except Exception:
            pass


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "gemini_configured" in data


def test_create_incident_offline(client, mocker):
    mocker.patch("services.gemini_service.is_available", return_value=False)
    payload = {
        "raw_report": "Severe flooding near Anna Nagar Bridge in Chennai. Approximately 150 people are stranded on rooftops.",
        "location_text": "Anna Nagar Bridge, Chennai",
        "latitude": 13.0878,
        "longitude": 80.2085,
        "is_demo": True,
    }
    res = client.post("/api/incidents", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "SUCCESS"
    assert "incident_id" in data
    assert data["incident"]["incident_type"] == "flood"
    assert data["risk_assessment"]["severity"] in ("HIGH", "CRITICAL", "MEDIUM")
    assert len(data["resource_plan"]["resources"]) > 0
    assert data["logistics"]["location_available"] is True


def test_validation_errors(client):
    # Too short report
    res = client.post("/api/incidents", json={"raw_report": "short"})
    assert res.status_code == 422

    # Non-json
    res = client.post("/api/incidents", data="not json", content_type="text/plain")
    assert res.status_code in (400, 415)


def test_operator_approval_workflow(client, mocker):
    mocker.patch("services.gemini_service.is_available", return_value=False)
    # Create incident first
    payload = {
        "raw_report": "Major earthquake in Coimbatore. Multiple buildings collapsed.",
        "location_text": "Coimbatore",
        "is_demo": True,
    }
    create_res = client.post("/api/incidents", json=payload)
    assert create_res.status_code == 201
    inc_id = create_res.get_json()["incident_id"]

    # Approve plan
    approval_payload = {
        "operator_name": "Commander Sarah Jenkins",
        "decision": "APPROVED",
        "notes": "Rescue teams mobilized to sector 4.",
    }
    appr_res = client.post(f"/api/incidents/{inc_id}/approve", json=approval_payload)
    assert appr_res.status_code == 200
    appr_data = appr_res.get_json()
    assert appr_data["decision"] == "APPROVED"
    assert appr_data["approved_by"] == "Commander Sarah Jenkins"
    assert "disclaimer" in appr_data

    # Check incident detail shows approved status
    get_res = client.get(f"/api/incidents/{inc_id}")
    assert get_res.status_code == 200
    inc_data = get_res.get_json()
    assert inc_data["incident"]["status"] == "APPROVED"
    assert inc_data["response_plan"]["approval_status"] == "APPROVED"


def test_priority_queue(client, mocker):
    mocker.patch("services.gemini_service.is_available", return_value=False)
    res = client.get("/api/queue")
    assert res.status_code == 200
    data = res.get_json()
    assert "queue" in data
    assert isinstance(data["queue"], list)


def test_resources_endpoint(client):
    res = client.get("/api/resources")
    assert res.status_code == 200
    data = res.get_json()
    assert "resources" in data
    assert "data_provenance" in data
    assert len(data["resources"]) > 0


def test_analytics_endpoint(client):
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_incidents" in data
    assert "by_severity" in data
    assert "agent_stats" in data


def test_persistence_after_db_reload(client, mocker):
    """Ensure created incidents and plans persist across new sessions/reloads."""
    mocker.patch("services.gemini_service.is_available", return_value=False)
    payload = {
        "raw_report": "Chemical plant leak reported in Ennore industrial corridor.",
        "location_text": "Ennore",
        "is_demo": True,
    }
    create_res = client.post("/api/incidents", json=payload)
    assert create_res.status_code == 201
    inc_id = create_res.get_json()["incident_id"]

    # Open a fresh database session completely separate from the API client
    db = SessionLocal()
    try:
        found = db.query(Incident).filter(Incident.id == inc_id).first()
        assert found is not None
        assert found.incident_type in ("gas_leak", "industrial_accident", "other")
        plan = db.query(ResponsePlan).filter(ResponsePlan.incident_id == inc_id).first()
        assert plan is not None
    finally:
        db.close()
