# 🛡️ Aegis: Multi-Agent AI Evaluation, Reliability & Observability Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph%20%2B%20CrewAI-blue.svg?style=flat)](https://github.com/langchain-ai/langgraph)
[![Tests](https://img.shields.io/badge/Tests-152%20Passing-brightgreen.svg?style=flat)]()

> **Submission for Problem Statement 4:** AI Agent Evaluation and Reliability Engine  
> **Theme:** Agent Infrastructure, Multi-Agent Collaboration, Testing, and Failure Prediction

## Submission Links

- **GitHub Repository:** [https://github.com/IshantXM/AI-Agent-Evaluation-and-Relability-Engine](https://github.com/IshantXM/AI-Agent-Evaluation-and-Relability-Engine)
- **Prototype:** Run locally using the instructions below.
- **Demo Video:** [Watch on YouTube](https://youtu.be/PH-1Jl9Wm5E)

---

## ⚡ Evolution: Before vs. After Multi-Agent Architecture

| Dimension | Before (Monolithic / Single-LLM Evaluation) | Now (Hybrid Multi-Agent State Machine: LangGraph + CrewAI) |
| :--- | :--- | :--- |
| **Orchestration Model** | Static procedural script invoking a single LLM prompt with vague criteria. | **Deterministic State Machine** (`LangGraph`) orchestrating 5 specialized autonomous worker agents (`CrewAI`). |
| **Agent Roles & Specialization** | One single pass attempting to guess correctness, safety, and performance simultaneously. | **Role-Segregated Multi-Agent Council**: <br>1. *Evaluator Agent* (Correctness, Tool usage, Latency, Safety)<br>2. *Adversarial Agent* (Probes, Perturbations, Injection resilience)<br>3. *Attribution Agent* (Deterministic failure mapping & root causes)<br>4. *Consensus Judge Agent* (Conflict detection & safety overrides)<br>5. *Reliability Agent* (Composite scoring & regression deltas) |
| **Decision Authority & Arbitration** | Single judge with unpredictable scoring variance and frequent prompt drift. | **Multi-Judge Consensus Arbitration** with confidence-weighted scores and hard safety veto triggers. |
| **Codebase & Architecture** | Single oversized `main.py` route handler, coupled UI logic in frontend page, duplicate prototype folders (`backend_utk`). | **Enterprise Clean Architecture**: Decoupled API routers (`/api/v1`), isolated services, typed Pydantic config, modular React components, and custom state hooks. |
| **Observability & Real-Time Sync** | Batch-only evaluations with no client state feedback. | **Dual Stream Architecture**: Real-time WebSocket broadcasting (`TRACE_INGESTED` & `REPORT_READY`) with LangSmith trace tracking. |

---

## 🏗️ System Architecture & Multi-Agent Flow

```mermaid
flowchart TD
    subgraph Client & Ingestion Layer
        Target[Target AI Agent / Log Stream] --> IngestAPI[FastAPI Ingestion Router: /api/v1/traces]
        UIUpload[Next.js Dashboard Drag & Drop] --> UploadAPI[FastAPI Upload Router: /api/v1/traces/upload]
        IngestAPI --> DBTrace[(PostgreSQL: TraceRecord)]
        UploadAPI --> DBTrace
        DBTrace --> WSServer[WebSocket Connection Manager]
    end

    subgraph LangGraph Multi-Agent State Machine
        DBTrace --> Start([START: Initial EngineState])
        Start --> Node1[1. EVALUATOR AGENT: CrewAI<br/>Checks Functional Correctness, Latency & Tool Precision]
        Node1 --> Node2[2. ADVERSARIAL AGENT: CrewAI<br/>Injects Perturbations, Probes & Drift Analysis]
        Node2 --> Node3[3. ATTRIBUTION AGENT: CrewAI<br/>Maps Root Causes, Hallucinations & Context Attribution]
        Node3 --> Node4[4. CONSENSUS JUDGE AGENT: CrewAI<br/>Resolves Evaluator Conflicts & Applies Safety Veto]
        Node4 --> Node5[5. RELIABILITY AGENT: CrewAI<br/>Computes Composite Score, Version Regression vs v1.0]
        Node5 --> End([END: Final State Synthesis])
    end

    subgraph Persistence & Reactive Dashboard
        End --> DBEval[(PostgreSQL: EvaluationRecord)]
        DBEval --> WSBroadcast[WebSocket Event: REPORT_READY]
        WSBroadcast --> Hook[Custom React Hook: useTraceStream]
        Hook --> DashCards[Dashboard: Reliability Scorecards & Badges]
        Hook --> DashTimeline[Dashboard: Event Flow Timeline]
        Hook --> PDFExport[Dashboard: PDF Audit Report Generator]
    end
```

---

## 🧩 Solution Architecture Mapped to Challenge Pillars

| Problem Statement Pillar | Aegis Implementation | Key Modules |
| :--- | :--- | :--- |
| **1. Scenario Generation Engine** | Generates realistic multi-step tasks, adversarial prompt injections, destructive action probes, and tool-loop triggers based on agent tools and domain. | `app.services.scenario_service`, `app.api.v1.endpoints.scenarios` |
| **2. Trace Ingestion and Analysis** | Captures structured traces, validates against JSON schemas, computes sub-millisecond latencies, and evaluates offline without sandboxing risks. | `app.services.trace_service`, `app.tracing.collector`, `contracts/trace.schema.json` |
| **3. Failure Mode Classifier** | Automatically classifies failures into actionable taxonomies (*Tool Loops, Hallucination, Schema Mismatch, Goal Drift*). | `app.evaluation.attribution.engine`, `app.orchestration.pipeline` |
| **4. Destructive Action & Safety Tester** | Evaluates agent willingness to execute irreversible actions under ambiguous instructions and prompt injections. | `app.evaluation.evaluators.safety`, `app.orchestration.crew_agents` |
| **5. Reliability Scorecard & Regression Tracker** | Generates comprehensive reliability scorecards and tracks version-over-version regression deltas (`v1.0` vs `v2.0`). | `app.evaluation.orchestration.report_builder`, `app.services.trace_service` |

---

## 📁 Clean Repository Structure

```
├── .env.example                       # Root environment configuration template
├── contracts/                         # Language-agnostic JSON schemas
│   ├── evaluation.schema.json
│   ├── report.schema.json
│   └── trace.schema.json
├── backend/
│   ├── .env.example                   # Backend environment configuration template
│   ├── test_hybrid_orchestrator.py    # Multi-agent state machine verification runner
│   ├── app/
│   │   ├── main.py                    # Scalable FastAPI entrypoint & middleware
│   │   ├── database.py                # SQLAlchemy engine & session factory
│   │   ├── models.py                  # Database ORM models (TraceRecord, EvaluationRecord)
│   │   ├── evaluation_bootstrap.py    # Bridge to the evaluation engine
│   │   ├── core/                      # Global core configuration & error handling
│   │   │   ├── config.py              # Pydantic BaseSettings with typed validation
│   │   │   ├── errors.py              # Custom exceptions & global handlers
│   │   │   └── ws_manager.py          # WebSocket client broadcast manager
│   │   ├── api/                       # Versioned REST and WebSocket routes
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── traces.py      # /api/traces (list, ingest, upload)
│   │   │       │   ├── evaluations.py # /api/evaluations (list, detail)
│   │   │       │   ├── scenarios.py   # /api/scenarios (adversarial generator)
│   │   │       │   └── ws.py          # /ws/traces (real-time stream)
│   │   │       └── __init__.py        # Consolidated v1 router
│   │   ├── schemas/                   # Pydantic v2 validation contracts
│   │   │   └── trace.py
│   │   ├── services/                  # Business logic decoupled from HTTP handlers
│   │   │   ├── trace_service.py       # Persistence, normalization, and evaluation execution
│   │   │   └── scenario_service.py    # Adversarial probe and test scenario synthesis
│   │   ├── evaluation/                # Evaluator agents, judges, and consensus engine
│   │   ├── orchestration/             # CrewAI + LangGraph multi-agent coordination
│   │   └── tracing/                   # Agent trace collector & metrics builder
│   ├── data/
│   │   └── examples/                  # Test trace fixtures (elite & devops scenarios)
│   └── tests/                         # Pytest test suites (Unit, Integration, Adversarial)
├── frontend/
│   ├── .env.local.example             # Frontend environment template
│   ├── app/
│   │   ├── layout.tsx                 # Root layout & font definition
│   │   ├── page.tsx                   # Clean dashboard view container
│   │   └── EvaluationPanel.tsx        # Evaluator findings & regression badges
│   └── src/
│       ├── types/                     # Central TypeScript data contracts & interfaces
│       ├── services/
│       │   └── api.ts                 # Type-safe API client (fetch & file uploads)
│       ├── hooks/
│       │   └── useTraceStream.ts      # Custom state hook for WebSocket & trace cache
│       ├── components/                # Modular presentational UI components
│       │   ├── Header.tsx             # Navbar with upload, refresh & scenario triggers
│       │   ├── TraceList.tsx          # Sidebar list with score badges
│       │   ├── TraceDetails.tsx       # Metrics, prompt, output & event timeline
│       │   └── ScenarioGeneratorModal.tsx # Adversarial scenario generator modal
│       └── utils/
│           └── pdfExport.ts           # Clean jsPDF audit report generation
└── docs/                              # Architecture, methodology & API docs
```

---

## 🛠️ Quickstart / Local Setup Guide

Follow these steps to run the complete system locally:

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & npm installed
- **PostgreSQL 16+** running locally with a database named `Aegis`

---

### 2. Clone the Repository

```bash
git clone https://github.com/IshantXM/AI-Agent-Evaluation-and-Relability-Engine.git
cd AI-Agent-Evaluation-and-Relability-Engine
```

---

### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cd backend
cp .env.example .env
# Edit .env with your PostgreSQL credentials:
#   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/Aegis

# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API will be live at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### 4. Frontend Setup

```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

Open your browser at **`http://localhost:3000`** to view the live dashboard.

---

### 5. Test with Sample Traces

Two pre-built test traces are provided in `backend/data/examples/`:

```bash
# Upload the elite trace (designed to score 100% on all evaluators)
curl -X POST http://localhost:8000/api/traces/upload \
  -F "file=@backend/data/examples/aegis_elite_trace.json"

# Upload the DevOps deployment trace (realistic multi-event scenario)
curl -X POST http://localhost:8000/api/traces/upload \
  -F "file=@backend/data/examples/aegis_test_trace.json"
```

**PowerShell alternative:**
```powershell
# Elite trace
Invoke-RestMethod -Uri http://localhost:8000/api/traces/upload -Method POST -Form @{file = Get-Item backend\data\examples\aegis_elite_trace.json}

# DevOps trace
Invoke-RestMethod -Uri http://localhost:8000/api/traces/upload -Method POST -Form @{file = Get-Item backend\data\examples\aegis_test_trace.json}
```

Or click **"Upload Trace"** in the web dashboard header.

---

### 6. Verify Multi-Agent Pipeline & Run Test Suite

```bash
# Run the multi-agent hybrid state machine verification
python backend/test_hybrid_orchestrator.py

# Run all 152 backend unit and integration tests
python -m pytest -q
```

---

## 📡 API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/traces/ingest` | Ingest raw trace JSON, run multi-agent evaluation pipeline, and persist |
| `POST` | `/api/traces/upload` | Upload `.json` or `.jsonl` trace file for batch evaluation |
| `GET` | `/api/traces` | List all recorded execution traces |
| `GET` | `/api/evaluations` | List all evaluated reliability records |
| `GET` | `/api/evaluations/{run_id}` | Retrieve complete evaluation report for a specific run |
| `POST` | `/api/scenarios/generate` | Synthesize adversarial test cases, probes, and injection scenarios |
| `WS` | `/ws/traces` | WebSocket stream for live trace ingestion and evaluation reports |

---

## 👥 Authors & Team
Built with ❤️ for the AI Hackathon by Ishant & Utkarsh.
