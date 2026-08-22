# Adversarial Testing

The adversarial subsystem models scenarios and evaluates trace behavior against
those scenarios. The current HTTP scenario endpoint generates scenario
metadata for realistic workflows, prompt injection, destructive actions, and
tool-loop drift. Standard trace evaluation does not implicitly execute those
scenarios; callers must provide configured scenarios to the evaluation service.

Results are aggregated separately from standard evaluator consensus and feed
the reliability assessor when supplied.
