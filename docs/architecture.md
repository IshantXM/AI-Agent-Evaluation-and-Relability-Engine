# Architecture

Aegis evaluates structured execution traces produced by an external target
agent or application. It does not launch arbitrary target agents.

```mermaid
flowchart TD
  A[Target Agent Execution] --> B[Trace Collector]
  B --> C[Trace Contract]
  C --> D[Evaluation Orchestrator]
  D --> E[Correctness]
  D --> G[Tool Use]
  D --> H[Safety]
  D --> I[Robustness]
  D --> J[Efficiency]
  E --> K[Critic Consensus]
  F --> K
  G --> K
  H --> K
  I --> K
  J --> K
  K --> L[Failure Attribution]
  L --> M[Reliability Assessment]
  M --> N[Regression Analysis]
  N --> O[Final Reliability Report]
```

The FastAPI boundary normalizes input, persists traces in PostgreSQL, invokes
the evaluation service, persists the report, and streams trace/report events
to the dashboard over WebSockets. Evaluation modules remain independent of
FastAPI and frontend code.
