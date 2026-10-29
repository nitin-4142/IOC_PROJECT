# AI Disaster Response Coordinator — Five-Agent Multi-Agent System

An AI-assisted emergency response platform that receives unstructured disaster reports, analyzes situational facts, assesses risk, recommends rescue resources from a configurable playbook, evaluates logistics, and generates an auditable, prioritized incident response plan with mandatory human-in-the-loop approval.

---

> **Operational Decision-Support Disclaimer**  
> This application is a decision-support prototype. It **never** claims that rescue teams have actually been dispatched, that hospitals have been contacted, or that a route is safe unless verified by an authorized real-world integration. Real-world dispatch is strictly separated from AI plan generation and requires explicit operator authorization.

---

## 1. Project Objective

In sudden-onset disasters (floods, earthquakes, fires, cyclones, industrial hazards), emergency coordination centers are flooded with unstructured, incomplete, and chaotic reports from public transmissions, hotlines, and field units.

The **AI Disaster Response Coordinator** organizes this raw incoming stream through five specialized, synchronized agents into structured, prioritized decision dossiers that emergency commanders can verify and authorize.

---

## 2. Multi-Agent Architecture

```
                       [ Incoming Emergency Report ]
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │        Agent 1: Emergency Intelligence Agent           │
        │  • Disaster categorization (flood, earthquake, fire)   │
        │  • Entity & location extraction                        │
        │  • Immediate threats detection                         │
        │  • Uncertainty & missing data flagging                 │
        │  (Google Gemini API or Deterministic Rule Fallback)    │
        └────────────────────────────┬───────────────────────────┘
                                     │ ExtractedIncident
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │            Agent 2: Risk Assessment Agent              │
        │  • Transparent deterministic Python scoring (0-100)    │
        │  • Severity rating: LOW, MEDIUM, HIGH, CRITICAL        │
        │  • Precautionary risk on missing population/data       │
        │  • Human review flag for uncertain assessments         │
        └────────────────────────────┬───────────────────────────┘
                                     │ RiskAssessmentOutput
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │          Agent 3: Resource Planning Agent              │
        │  • Disaster playbook resource matching                 │
        │  • Scaling based on affected population scale          │
        │  • Sample depot availability verification (DEMO_DATA)  │
        │  • Shortfall detection against active inventory        │
        └────────────────────────────┬───────────────────────────┘
                                     │ ResourcePlanOutput
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │       Agent 4: Logistics and Routing Agent             │
        │  • Coordinates validation & geocoding safety checks    │
        │  • Haversine & road factor distance estimation         │
        │  • Sample shelter & medical facility discovery         │
        │  • Route unverified / road condition warning flags     │
        └────────────────────────────┬───────────────────────────┘
                                     │ LogisticsOutput
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │     Agent 5: Coordination and Monitoring Agent         │
        │  • Unified response plan synthesis                     │
        │  • Conflict detection across active incident queue     │
        │  • Operator follow-up questions generation             │
        │  • State machine management (PLAN_READY -> APPROVED)   │
        │  • Comprehensive audit logging & event history         │
        └────────────────────────────┬───────────────────────────┘
                                     │ CoordinationOutput
                                     ▼
                     [ Persistent SQLite Storage ]
                                     │
                                     ▼
             [ Flask REST API ] <---> [ React Operations UI ]
```

---

## 3. The Five Specialized Agents

### Agent 1: Emergency Intelligence Agent (`backend/agents/intelligence_agent.py`)
- **Role:** Natural language understanding and fact extraction.
- **Classification:** Categorizes disasters into `flood`, `earthquake`, `fire`, `cyclone`, `landslide`, `building_collapse`, `gas_leak`, `industrial_accident`, `tsunami`, `epidemic`, or `other`.
- **Integrity Rule:** Never invents GPS coordinates, casualty counts, or unverified claims.
- **Fallback:** When Gemini is unavailable, parses reports using deterministic regex and keyword patterns.

### Agent 2: Risk Assessment Agent (`backend/agents/risk_agent.py`)
- **Role:** Quantitative severity and risk prioritization.
- **Scoring Function:** Calculates a transparent 0–100 score based on 6 weighted factors:
  - Population Scale (0–25 pts)
  - Confirmed Injuries / Medical Vulnerabilities (0–20 pts)
  - Disaster Baseline Severity (0–20 pts)
  - Active Immediate Threats (0–15 pts)
  - Missing Persons (0–10 pts)
  - Missing Critical Information (0–10 pts precautionary risk)
- **Integrity Rule:** Risk scores are calculated deterministically in Python arithmetic—never accepted unverified from a language model.

### Agent 3: Resource Planning Agent (`backend/agents/resource_agent.py`)
- **Role:** Playbook-based tactical equipment and personnel recommendation.
- **Playbook:** Maps incident types and severity tiers to recommended rescue boats, ambulances, fire engines, emergency shelters, food rations, and medical personnel.
- **Integrity Rule:** Resource availability is labelled `DEMO_DATA` / `UNKNOWN`. Units are never claimed to be physically deployed.

### Agent 4: Logistics and Routing Agent (`backend/agents/logistics_agent.py`)
- **Role:** Spatial proximity estimation and depot matching.
- **Routing:** Calculates straight-line and road-factor (1.4×) estimates when coordinates are supplied. If coordinates are missing, returns `location_available: false` and flags routing as unverified.
- **Integrity Rule:** Flags unverified road conditions and never fabricates transit safety.

### Agent 5: Coordination and Monitoring Agent (`backend/agents/coordination_agent.py`)
- **Role:** End-to-end plan synthesis and human authorization gatekeeper.
- **Conflict Management:** Checks for inventory shortfalls against active operations.
- **Workflow State Machine:** `NEW` → `UNDER_REVIEW` → `AWAITING_INFORMATION` → `PLAN_READY` → `APPROVED` → `IN_PROGRESS` → `RESOLVED`.
- **Integrity Rule:** Mandates explicit human operator authorization before recording plan approval.

---

## 4. Technology Stack

- **Backend:**
  - Python 3.12 / 3.13
  - Flask & Flask-CORS
  - Google GenAI SDK (`google-genai`)
  - Pydantic v2 for strict schema validation
  - SQLAlchemy 2.0 with SQLite persistent local storage
  - Pytest & Pytest-Mock for automated unit & integration testing
- **Frontend:**
  - React 18 with Vite
  - Tailwind CSS for Dark Navy Tactical Operations styling
  - React Leaflet & Leaflet for geospatial tracking
  - Recharts for incident telemetry & severity charts
  - Lucide React for tactical UI icons
  - Axios for centralized API client communication

---

## 5. Folder Structure

```
disaster-response-coordinator/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intelligence_agent.py
│   │   ├── risk_agent.py
│   │   ├── resource_agent.py
│   │   ├── logistics_agent.py
│   │   └── coordination_agent.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── incident.py
│   │   ├── assessment.py
│   │   ├── resource.py
│   │   ├── plan.py
│   │   └── execution.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_service.py
│   │   ├── resource_service.py
│   │   └── routing_service.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   └── test_api.py
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── orchestrator.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── UI.jsx
│   │   ├── hooks/
│   │   │   └── useApi.js
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ReportIncident.jsx
│   │   │   ├── IncidentList.jsx
│   │   │   ├── IncidentDetail.jsx
│   │   │   ├── IncidentMap.jsx
│   │   │   ├── ResourceInventory.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── SystemActivity.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
├── sample_data/
│   └── incidents.json
├── scripts/
│   └── seed_demo.py
└── README.md
```

---

## 6. Installation & Execution (Windows Instructions)

Open two separate Command Prompt or PowerShell terminals on Windows.

### Terminal 1: Backend Setup & Execution

```powershell
# 1. Navigate to the backend directory
cd "c:\Users\nitin\OneDrive\Documents\disaster control\disaster-response-coordinator\backend"

# 2. Activate Python Virtual Environment (already created)
.\venv\Scripts\Activate.ps1

# 3. (Optional) Configure Gemini API Key if you have one
# If omitted or left as default, the system automatically runs in 100% offline fallback mode
Copy-Item .env.example .env
# Edit .env with your GEMINI_API_KEY if desired

# 4. Run Automated Pytest Suite to verify all 47 tests pass
python -m pytest tests -v

# 5. Start the Flask Backend Server (Runs on port 5000)
python app.py
```

*The backend server will initialize the SQLite database (`disaster_response.db`) and seed the demo resource inventory automatically on first start.*

---

### Terminal 2: Frontend Setup & Execution

```powershell
# 1. Navigate to the frontend directory
cd "c:\Users\nitin\OneDrive\Documents\disaster control\disaster-response-coordinator\frontend"

# 2. Start Vite Development Server (Runs on port 5173)
npm run dev
```

*Open your web browser and navigate to: **`http://localhost:5173`***

---

### Terminal 3 (Optional): Seed Sample Disasters

To populate the database with realistic demonstration emergencies (floods, earthquakes, chemical fires):

```powershell
cd "c:\Users\nitin\OneDrive\Documents\disaster control\disaster-response-coordinator"
.\backend\venv\Scripts\python.exe scripts\seed_demo.py
```

---

## 7. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & dependency status (database, AI mode) |
| `POST` | `/api/incidents` | Submit raw emergency report; executes 5-agent pipeline |
| `GET` | `/api/incidents` | List paginated incidents with priority sorting & filters |
| `GET` | `/api/incidents/<id>` | Full incident dossier, risk factors, recommendations, and agent execution times |
| `PATCH` | `/api/incidents/<id>/status` | Update incident status (`UNDER_REVIEW`, `IN_PROGRESS`, `RESOLVED`, etc.) |
| `POST` | `/api/incidents/<id>/approve` | Authorize and record operator approval for a response plan |
| `GET` | `/api/incidents/<id>/events` | Incident audit trail and lifecycle event log |
| `GET` | `/api/queue` | Active incident priority queue sorted by risk score |
| `GET` | `/api/resources` | Sample resource inventory and data provenance |
| `GET` | `/api/analytics` | Aggregated telemetry, severity breakdown, and agent latencies |
| `POST` | `/api/demo/reset` | Safeguarded reset for demo incidents only (`is_demo=true`) |

---

## 8. Automated Testing Evidence

All 47 tests run completely offline with mocked AI and external network interfaces:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\nitin\OneDrive\Documents\disaster control
collected 47 items

backend/tests/test_agents.py::TestIntelligenceAgent (9 tests) ............. PASSED
backend/tests/test_agents.py::TestRiskAgent (7 tests) ...................... PASSED
backend/tests/test_agents.py::TestResourceAgent (5 tests) .................. PASSED
backend/tests/test_agents.py::TestLogisticsAgent (4 tests) ................. PASSED
backend/tests/test_agents.py::TestCoordinationAgent (5 tests) .............. PASSED
backend/tests/test_agents.py::TestOrchestrator (2 tests) ................... PASSED
backend/tests/test_agents.py::TestSchemas (5 tests) ........................ PASSED
backend/tests/test_agents.py::TestRoutingService (2 tests) ................. PASSED
backend/tests/test_api.py::test_health_endpoint ............................ PASSED
backend/tests/test_api.py::test_create_incident_offline .................... PASSED
backend/tests/test_api.py::test_validation_errors .......................... PASSED
backend/tests/test_api.py::test_operator_approval_workflow ................. PASSED
backend/tests/test_api.py::test_priority_queue ............................. PASSED
backend/tests/test_api.py::test_resources_endpoint ......................... PASSED
backend/tests/test_api.py::test_analytics_endpoint ......................... PASSED
backend/tests/test_api.py::test_persistence_after_db_reload ................ PASSED

============================= 47 passed in 1.48s ==============================
```

---

## 9. Security & Reliability Highlights

1. **Deterministic Fallbacks:** The platform functions seamlessly offline or during API quota exhaustion without crashing.
2. **Untrusted Input Protection:** Prompt injection attempts embedded inside disaster reports cannot override agent policies or schema contracts.
3. **Auditability:** Every agent execution, latency metric, fallback trigger, and operator approval is permanently recorded in SQLite.
4. **No Real-world Side Effects:** Real-world dispatch is strictly prevented by software architecture.
