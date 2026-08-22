# 🛡️ Aegis: AI Agent Evaluation & Reliability Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-152%20Passing-brightgreen.svg?style=flat)]()

> **Submission for Problem Statement 4:** AI Agent Evaluation and Reliability Engine  
> **Theme:** Agent Infrastructure, Testing, and Failure Prediction

## Submission Links

- **Prototype:** Not hosted yet. Run locally using the instructions below, or replace this line with the deployed dashboard URL before submission.
- **Demo video:** Mandatory submission item. Add the final video link here; keep the walkthrough under 10 minutes.
- **Source:** This GitHub repository contains the backend, dashboard, trace fixtures, evaluator tests, and deployment configuration.

---

## What Aegis Actually Does

Aegis evaluates structured execution traces produced by an external agent or
application. It does not launch arbitrary agents, execute tools on their
behalf, or provide a sandbox. The trace collector is an SDK utility for code
that wants to record an execution; the API accepts already-produced traces.

Given a trace, Aegis normalizes and persists it, runs six deterministic
evaluators, optionally asks a configured Gemini judge for a task-level review,
calculates consensus and reliability, and builds a versioned report. Benchmark,
adversarial, ablation, and attribution components are available as separate
evaluation subsystems.

---

## 🧩 Solution Architecture Mapped to Challenge Pillars

| Problem Statement Pillar | Aegis Implementation | Key Modules |
| :--- | :--- | :--- |
| **1. Scenario Generation Engine** | Generates realistic and adversarial test scenarios across task domains, prompt perturbations, and edge cases. | `app.evaluation.adversarial.engine`, `app.evaluation.benchmark` |
| **2. Trace Ingestion and Analysis** | Captures or accepts structured traces and evaluates them offline; it is not a sandbox or replay executor. | `app.tracing.collector`, `contracts/trace.schema.json` |
| **3. Failure Mode Classifier** | Automatically classifies failures into actionable taxonomies (*Tool Loops, Hallucination, Schema Mismatch, Goal Drift*). | `app.evaluation.attribution.engine`, `app.evaluation.attribution.rules` |
| **4. Destructive Action & Safety Tester** | Evaluates agent willingness to execute irreversible actions under ambiguous instructions and prompt injections. | `app.evaluation.evaluators.safety`, `app.evaluation.evaluators.robustness` |
| **5. Reliability Scorecard & Regression Tracker** | Generates comprehensive reliability scorecards and tracks version-over-version regression deltas (`v1.0` vs `v2.0`). | `app.evaluation.orchestration.report_builder`, `app.evaluation.reliability.regression` |

---


- **Multi-Dimensional Evaluator Suite**:
  - 🎯 **Correctness**: Output verification against ground truth, task constraints, and schema conformance.
  - ⚓ **Grounding & Factuality**: Hallucination detection verifying claims against execution context and retrieved documents.
  - 🛠️ **Tool Usage**: Accuracy of tool selection, argument parameter validation, and recovery handling.
  - 🛡️ **Safety & Policy**: Harmful content detection, prompt injection resilience, and policy compliance.
  - 🧪 **Robustness & Perturbation**: Resilience testing against adversarial inputs and non-deterministic variations.
  - ⚡ **Efficiency**: Automated high-precision latency measurement, token budgets, and cost attribution.

- **Deterministic Failure Attribution**:
  - Pinpoints exact root causes (*Hallucination, ToolExecutionError, SchemaMismatch, Timeout*) with concrete evidence chains.

- **Real-Time Trace Streaming & WebSocket Timeline**:
  - Live visual inspector tracking agent thoughts, tool calls, and LLM completions as they happen.

- **Coverage-Aware Reliability Assessment & Regression Tracking**:
  - Confidence-weighted consensus across all evaluators.
  - Automated version-over-version regression delta (`v1.0` vs `v2.0`).

- **Automated High-Precision Instrumentation (`TraceCollector` SDK)**:
  - Context-manager spans (`with collector.span(...)`) that automatically record sub-millisecond latencies, token counts, and cost metrics.

---

## 🏗️ Architecture & Pipeline

```
               Autonomous AI Agent / Application
                               │
                [TraceCollector SDK / API Ingest]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INGESTION & TRACE NORMALIZATION                          │
│    • Schema Validation (JSON Contract)                      │
│    • Automated Latency & Token Metric Aggregation           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PARALLEL EVALUATOR ENGINE                                │
│    ├─► Correctness Evaluator                                │
│    ├─► Grounding & Hallucination Evaluator                  │
│    ├─► Tool Call Evaluator                                  │
│    ├─► Safety & Policy Evaluator                            │
│    ├─► Robustness & Adversarial Evaluator                   │
│    └─► Efficiency Evaluator                                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CONSENSUS & ATTRIBUTION ENGINE                           │
│    • Confidence-Weighted Evaluator Consensus                │
│    • Deterministic Failure Attribution & Root Causes        │
│    • Coverage Calculation                                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RELIABILITY REPORT BUILDER                               │
│    • Overall Score (0.0 to 1.0)                             │
│    • Reliability Status: RELIABLE | DEGRADED | UNRELIABLE   │
│    • Actionable Recommendations & Fixes                     │
│    • Version Regression Analysis (vs previous run)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ PostgreSQL Persistence      │ │ Next.js Real-time Dashboard │
│ (`traces`, `eval_records`)  │ │ WebSocket Timeline & Charts │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 🛠️ Quickstart / Local Setup Guide

Follow these steps to run the complete system locally:

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & npm installed
- **PostgreSQL 16+**

---

### 2. Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Install dependencies
pip install -r ../requirements.txt

# 3. Configure Environment Variables
# Copy example env file
cp .env.example .env

# Edit .env with your PostgreSQL credentials:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/Aegis
# CORS_ORIGINS=http://localhost:3000

# 4. Run database migrations & start FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be live at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

### Optional Gemini LLM Judge

The built-in evaluators remain deterministic. To add a task-level Gemini judge,
configure Gemini's OpenAI-compatible chat-completions endpoint before starting
the backend:

```bash
AEGIS_JUDGE_API_KEY=your-key
AEGIS_JUDGE_MODEL=gemini-1.5-flash
AEGIS_JUDGE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

The judge result is added to consensus and the saved evaluation record. If no
`AEGIS_JUDGE_API_KEY` is set, evaluations run fully offline with the existing
deterministic evaluators.

---

### 3. Frontend Setup

```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Optional: copy .env.local.example to .env.local and set the remote API URL
# NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com

# Start the Next.js development server
npm run dev
```
Open your browser at **`http://localhost:3000`** to view the live dashboard.

For remote teams, deploy the backend and frontend separately. Set
`NEXT_PUBLIC_API_BASE_URL` to the public backend URL and set backend
`CORS_ORIGINS` to the public frontend URL (comma-separated values are allowed).
The frontend derives its WebSocket URL from the API URL, so trace events and
reports continue to stream remotely.

### Functional Prototype Walkthrough

1. Start the backend and frontend.
2. Upload a `.json` or `.jsonl` agent trace from the dashboard.
3. Review the six evaluator dimensions, failures, reliability score, and regression data.
4. Open the Scenario Generator tab to create realistic and adversarial test cases.
5. Configure the optional Gemini judge to review deterministic evaluator evidence and influence consensus/reliability.

This demonstrates trace ingestion, scenario metadata generation, evaluator
analysis, safety testing, failure attribution, and reliability scorecards from
the hackathon problem statement.

### Documentation

- [Architecture](docs/architecture.md)
- [Evaluation methodology](docs/evaluation-methodology.md)
- [Evaluation contract](docs/evaluation-contract.md)
- [Benchmarks](docs/benchmarks.md)
- [Adversarial testing](docs/adversarial-testing.md)
- [Ablation study](docs/ablation-study.md)
- [Reliability](docs/reliability.md)
- [Development](docs/development.md)
- [Contributing](docs/contributing.md)

### Repository Structure

```text
backend/app/       FastAPI boundary, tracing, contracts, and evaluation engine
backend/tests/     Unit, integration, reliability, benchmark, and experiment tests
contracts/         JSON interchange schemas
docs/              Architecture and methodology documentation
frontend/          Next.js dashboard
scripts/           Thin command-line entry points over application services
data/              Reserved for generated or user-provided datasets
```

### Limitations

The current prototype evaluates supplied traces; it does not run target
agents. Adversarial scenarios are generated as metadata and only influence a
run when explicitly passed to the evaluation service. Attribution is available
as a subsystem but is not yet included in the persisted API report. WebSocket
updates currently cover trace ingestion and report readiness rather than every
agent step. Scores are diagnostic evidence, not a guarantee of production
correctness or safety.

---

### 4. Run Test Suite & Simulations

#### A. Run All Backend Tests
```bash
python -m pytest -q
python -m compileall backend
```

#### B. Run Simulated Agent Execution
```bash
# In the project root
python run_mock_agent.py
```
This will:
1. Simulate an external agent trace with real-time spans.
2. Automatically calculate exact latency, tokens, tool calls, and costs.
3. Ingest the trace and run the full evaluation engine.
4. Broadcast live events to the dashboard at `http://localhost:3000`.

#### C. Run the Service Scripts

```bash
python scripts/run_evaluation.py backend/tests/fixtures/traces/correct_trace.json
python scripts/run_benchmark.py
python scripts/run_ablation.py backend/tests/fixtures/traces/correct_trace.json
```

These scripts call the existing application composition and evaluation
services; they do not contain a second implementation of scoring logic.

---

## 📡 API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/traces/ingest` | Ingest raw trace, evaluate across all dimensions, and persist |
| `GET` | `/api/traces` | List all recorded execution traces |
| `GET` | `/api/evaluations` | List all evaluated reliability records |
| `GET` | `/api/evaluations/{run_id}` | Get complete evaluation report for a specific run |
| `WS` | `/ws/traces` | WebSocket stream for live timeline and report notifications |

---

## 🧪 Evaluation Methodology

For full scientific documentation and experimental design of the leave-one-evaluator-out ablation study, see [`docs/ablation-study.md`](docs/ablation-study.md).

---

## 👥 Authors & Team
Built with ❤️ for the AI Hackathon by Ishant & Utkarsh.
