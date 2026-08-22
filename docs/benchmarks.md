# Benchmarks

A benchmark corpus is a JSON array of `BenchmarkCase` definitions. Each case
contains an identifier, name, trace fixture filename, category, difficulty,
and expected evaluator verdict/score ranges. `BenchmarkRunner` loads the case,
reads the referenced trace, evaluates it through `EvaluationPipeline`, and
computes case and evaluator accuracy.

```text
Benchmark Case -> Agent Trace -> Evaluation Pipeline -> Metrics
```

The bundled corpus is under `backend/tests/fixtures/benchmarks/` and is tested
by the benchmark test package.
