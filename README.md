# 🛡️ Aegis: AI Agent Evaluation & Reliability Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black.svg?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-152%20Passing-brightgreen.svg?style=flat)]()

> **Submission for Problem Statement 4:** AI Agent Evaluation and Reliability Engine  
> **Theme:** Agent Infrastructure, Testing, and Failure Prediction

---

## 🎯 Problem Context & Vision

Autonomous AI agents fail on up to **70% of real-world tasks** due to tool-call loops, hallucinated confidence, destructive actions, and silent goal drift. Most teams only test agents against a handful of manual prompts.

**Aegis** serves as **Continuous Integration (CI) for Autonomous Agents**: it continuously captures execution traces, runs adversarial perturbations, categorizes failure modes deterministically, and generates versioned reliability scorecards.

---

## 🧩 Solution Architecture Mapped to Challenge Pillars

| Problem Statement Pillar | Aegis Implementation | Key Modules |
| :--- | :--- | :--- |
| **1. Scenario Generation Engine** | Generates realistic and adversarial test scenarios across task domains, prompt perturbations, and edge cases. | `app.evaluation.adversarial.engine`, `app.evaluation.benchmark` |
| **2. Sandboxed Replay Harness** | Captures execution traces with `TraceCollector`, enabling sub-millisecond replay and deterministic offline evaluations. | `app.tracing.collector`, `contracts/trace.schema.json` |
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
- **PostgreSQL** (or SQLite zero-config fallback)

---

### 2. Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure Environment Variables
# Copy example env file
cp .env.example .env

# Edit .env with your PostgreSQL credentials (or leave default for local SQLite):
# DATABASE_URL=postgresql://postgres:password@localhost:5432/Aegis

# 4. Run database migrations & start FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be live at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Setup

```bash
# In a new terminal, navigate to the frontend directory
cd frontend-utk

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
Open your browser at **`http://localhost:3000`** to view the live dashboard.

---

### 4. Run Test Suite & Simulations

#### A. Run All Backend Unit Tests (152 Tests)
```bash
python -m pytest backend/tests/
```

#### B. Run Simulated Agent Execution
```bash
# In the project root
python run_mock_agent.py
```
This will:
1. Simulate an autonomous coding agent with real-time spans.
2. Automatically calculate exact latency, tokens, tool calls, and costs.
3. Ingest the trace and run the full evaluation engine.
4. Broadcast live events to the dashboard at `http://localhost:3000`.

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
