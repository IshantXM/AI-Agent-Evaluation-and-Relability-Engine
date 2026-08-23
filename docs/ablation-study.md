# Ablation Study Methodology

## Purpose

Aegis uses ablation to measure how much each evaluator contributes to a final
reliability score. This is a diagnostic experiment for engineering decisions:
it helps a team find redundant, high-value, or unstable evaluators before
changing the production evaluation policy.

## Experimental design

For one `AgentTrace`, `AblationRunner` executes:

1. A baseline with the selected evaluator set.
2. One case per evaluator, with exactly that evaluator removed.
3. Optional repeated trials for every case.

Cases can run concurrently with a configurable `max_concurrency`, or
sequentially when evaluator implementations have stateful external
dependencies.

The implementation lives in
`backend/app/evaluation/ablation/{models,metrics,runner}.py`; its public API is
exported from `backend/app/evaluation/ablation/__init__.py`.

## Running an experiment

The runner is currently an application/library API rather than a public HTTP
endpoint. A minimal experiment is:

```python
from backend.app.evaluation.ablation import AblationRunner

report = await AblationRunner(orchestrator).run(
		trace,
		 evaluators=["correctness", "tool_use", "safety"],
		trials=3,
		parallel=True,
		max_concurrency=4,
)
```

The test suite provides deterministic examples in
`backend/tests/evaluation/test_ablation_runner.py` and
`backend/tests/evaluation/test_ablation_metrics.py`.

## Metrics and interpretation

The score is the arithmetic mean of valid evaluator scores. For each removed
evaluator:

- `score_delta = ablated_score - baseline_score`
- Relative impact is `score_delta / baseline_score` when the baseline is not zero.
- A negative delta means the removed evaluator was contributing positively to
	the measured score.
- A positive delta means the evaluator was lowering the measured score or
	exposing disagreement.

The report ranks completed cases by absolute impact. Relative impact is
excluded when the baseline is zero because the ratio is undefined.

## Failure handling

Evaluator errors create a `FAILED` case with the original error type and
message. Failed cases do not influence impact rankings. Baseline evaluator
errors are excluded from the baseline mean, matching the standard orchestrator
behavior; an ablated case with no valid results fails instead of silently
becoming a zero score.

## Repeated trials and metadata

`trials` defaults to one. For repeated trials, each case reports mean score,
population standard deviation, minimum, and maximum. These are descriptive
statistics, not confidence intervals or significance tests.

Each report records evaluator order, removed evaluators, methodology/version,
execution mode, concurrency limit, trial count, and adversarial scenario
count. The current implementation does not claim a random seed because it
does not control a random-number generator.

## Limitations

This is not a causal experiment. Results depend on the selected trace, the
evaluator scoring rules, and any external state used by evaluators. A single
trace does not represent production traffic, evaluator dependence is not
modeled, and parallel execution may differ from sequential execution for
stateful integrations. Teams should compare multiple representative traces
and review the raw evaluator evidence before removing an evaluator.
