# Ablation Study Methodology

This subsystem performs a leave-one-evaluator-out experiment. It first runs
the selected evaluator list as the baseline, then reruns the same trace once
for each evaluator with exactly that evaluator removed.

## Scores and impact

The score is the arithmetic mean of valid evaluator scores. For a case,
`score_delta = ablated_score - baseline_score`; a negative delta means that
removing the evaluator reduced the score. Relative impact is
`(ablated_score - baseline_score) / baseline_score`.

Relative impact is `None` when the baseline is zero because the denominator is
zero and the ratio is mathematically undefined. Such a case can still retain
its absolute score delta, but it is excluded from relative-impact ranking.

## Failures

An evaluator execution error in an ablated run produces a `FAILED` case. The
case has no ablated score, delta, or impact direction, and preserves the error
type and message. Failed cases do not affect the most- or least-impactful
conclusions. Baseline evaluator errors are excluded from the baseline mean to
preserve the existing evaluation behavior; an ablation case that has no valid
results fails rather than becoming a zero score.

## Repeated trials

`trials` defaults to one. When it is greater than one, each leave-one-out case
is executed repeatedly. The case stores each trial result and reports the
mean, population standard deviation, minimum, and maximum ablated score.
These descriptive statistics do not establish confidence intervals,
statistical significance, or causal significance.

## Reproducibility metadata

Reports record the evaluator list and order, removed evaluators, methodology
name and version, parallel/sequential mode, concurrency limit, trial count,
and adversarial scenario count. No random seed is claimed because this
pipeline does not currently control a random-number generator.

## Limitations

This is a diagnostic comparison, not a causal experiment. It uses one trace
unless callers provide repeated trials, does not model evaluator dependence,
does not calculate inferential statistics, and does not guarantee that
parallel execution is equivalent for stateful external evaluators.
