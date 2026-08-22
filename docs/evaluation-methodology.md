# Evaluation Methodology

A trace is evaluated by independent deterministic evaluators for correctness,
grounding, tool use, safety, robustness, and efficiency. The orchestrator runs
them asynchronously and isolates evaluator errors. The critic calculates a
confidence-weighted consensus and records conflicts. An optional Gemini judge
then reviews the trace, evaluator evidence, and deterministic consensus. Its
review is fused into consensus score and confidence before reliability
assessment; it is not a seventh evaluation dimension.

The final report is coverage-aware: missing dimensions do not silently count
as passing. Scores are normalized to the interval $[0, 1]$ and raw evidence is
retained in each evaluator result.
