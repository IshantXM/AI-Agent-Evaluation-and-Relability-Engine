# Evaluation Contract

The JSON contracts at `contracts/` are interchange schemas for traces,
evaluation results, and reports. Runtime Pydantic models are maintained under
`backend/app/evaluation/core/`; `backend/app/contracts/` provides explicit
runtime contract exports without duplicating those definitions.

Flow:

```text
trace.schema.json -> AgentTrace -> EvaluationResult[] -> ConsensusResult
                                    -> ReliabilityReport
```

The API accepts a normalized trace payload and persists the raw trace together
with the complete evaluation artifact. Schema files are documentation and
interchange contracts; runtime validation is performed by Pydantic models and
normalization at the API boundary.
