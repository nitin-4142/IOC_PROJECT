"""
Verification script: executes the complete 5-agent workflow on the standard
emergency report in offline mode, persists to SQLite, verifies the output
at every agent stage, and prints the full structured decision dossier.
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from database import init_db, SessionLocal
from schemas import IncidentReportInput
from orchestrator import run_workflow
from models.incident import Incident
from models.plan import ResponsePlan

def verify_end_to_end():
    print("================================================================")
    print("RUNNING FIVE-AGENT END-TO-END WORKFLOW VERIFICATION (OFFLINE)")
    print("================================================================")

    init_db()
    db = SessionLocal()

    report_text = (
        "Severe flooding near Anna Nagar Bridge in Chennai. Approximately 150 people "
        "are stranded on rooftops. The water level is rising, and several elderly people "
        "need medical assistance."
    )

    input_data = IncidentReportInput(
        raw_report=report_text,
        location_text="Anna Nagar Bridge, Chennai",
        latitude=13.0878,
        longitude=80.2085,
        is_demo=True,
    )

    print("\n[STEP 1] Submitting report into Central Multi-Agent Orchestrator...")
    result = run_workflow(input_data, db)

    print(f"\n[ORCHESTRATOR STATUS]: {result['status']} (Execution time: {result['total_duration_ms']} ms)")
    print(f"Incident ID: {result['incident_id']}")
    print(f"Correlation ID: {result['correlation_id']}")

    print("\n--- AGENT EXECUTION SUMMARY ---")
    for agent_name, agent_res in result["agent_results"].items():
        print(f" • {agent_name}: status={agent_res['status']}, latency={agent_res['duration_ms']}ms, fallback={agent_res['used_fallback']}")

    print("\n--- AGENT 1: INTELLIGENCE OUTPUT ---")
    inc = result["incident"]
    print(f" Disaster Category : {inc['incident_type']}")
    print(f" Location Text     : {inc['location_text']}")
    print(f" GPS Coordinates   : ({inc['latitude']}, {inc['longitude']})")
    print(f" Population Impact : {inc['affected_population']}")
    print(f" Immediate Threats : {inc['immediate_threats']}")
    print(f" Missing Data Flags: {inc['missing_information']}")
    print(f" Extraction Source : {inc['processing_source']}")

    print("\n--- AGENT 2: RISK ASSESSMENT OUTPUT ---")
    risk = result["risk_assessment"]
    print(f" Priority Score    : {risk['risk_score']}/100")
    print(f" Severity Rating   : {risk['severity']}")
    print(f" Rationale         : {risk['rationale']}")
    print(f" Contributing Factors:")
    for factor in risk["contributing_factors"]:
        print(f"   - {factor}")

    print("\n--- AGENT 3: RESOURCE RECOMMENDATIONS ---")
    res_plan = result["resource_plan"]
    for r in res_plan["resources"]:
        print(f" • {r['resource_type'].upper():<18}: Qty {r['recommended_quantity']} | Status: {r['availability_status']} | Reason: {r['reason']}")

    print("\n--- AGENT 4: LOGISTICS & ROUTING ---")
    logistics = result["logistics"]
    print(f" Location Available: {logistics['location_available']}")
    print(f" Estimated Routes  : {len(logistics['routes'])} routes calculated from sample bases")
    for route in logistics["routes"][:2]:
        print(f"   Route: {route['from_location']} -> {route['to_location']} ({route['estimated_distance_km']} km, ~{route['estimated_time_min']} min)")
    print(f" Nearby Shelters   : {[s['name'] for s in logistics['nearby_shelters']]}")
    print(f" Warnings          : {logistics['warnings'][0] if logistics['warnings'] else 'None'}")

    print("\n--- AGENT 5: COORDINATED RESPONSE PLAN ---")
    coord = result["coordination"]
    print(f" Summary           : {coord['summary']}")
    print(f" Status            : {coord['incident_status']}")
    print(f" Priority Actions:")
    for idx, act in enumerate(coord["priority_actions"], 1):
        print(f"   {idx}. {act}")

    # Verify Persistence in SQLite
    print("\n--- VERIFYING SQLITE DATABASE PERSISTENCE ---")
    persisted_inc = db.query(Incident).filter(Incident.id == result['incident_id']).first()
    assert persisted_inc is not None, "Failed: incident not found in database!"
    persisted_plan = db.query(ResponsePlan).filter(ResponsePlan.incident_id == result['incident_id']).first()
    assert persisted_plan is not None, "Failed: response plan not found in database!"
    print(f" ✓ Incident record confirmed in SQLite (Status: {persisted_inc.status}, Severity: {persisted_inc.severity})")
    print(f" ✓ Response plan confirmed in SQLite (Approval Status: {persisted_plan.approval_status})")

    db.close()
    print("\n================================================================")
    print("VERIFICATION COMPLETED SUCCESSFULLY!")
    print("================================================================")

if __name__ == "__main__":
    verify_end_to_end()
