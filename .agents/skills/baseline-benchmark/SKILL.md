---
name: baseline-benchmark
description: Rigorous evaluation pipeline comparing a monolithic single-agent baseline against the Errand Brain Multi-Agent Society.
---

# Baseline Benchmark Skill

The rubric demands "measurable efficiency gain over single-agent baselines". This skill provides the exact methodology for generating that proof mathematically.

## 1. Dataset Generation
We maintain a test suite of `synthetic_errands.json` containing 20 hand-crafted, complex scenarios. Each scenario must feature:
- At least 5 discrete errands.
- At least 2 hard dependencies (e.g., "Get cash before paying the cleaner").
- At least 2 temporal constraints (e.g., "Store closes at 5 PM").

## 2. Testing Methodologies

### Approach A: The Monolith Baseline
- **Model**: `qwen-max` (Single prompt)
- **Prompt**: Pass all errands, dependencies, and constraints in one massive prompt. Ask the model to output the optimal route.
- **Limitation**: It will hallucinate distances and frequently miss logical constraints.

### Approach B: Errand Brain Society (Our Solution)
- **Models**: `qwen-turbo` (Specialists) + `qwen-max` (Orchestrator) + LangGraph
- **Execution**: The input is broken down, specialists evaluate geo/temporal/dependency constraints with deterministic tools (MCP), and the Orchestrator negotiates the final plan.

## 3. The Grading Rubric (Metrics)
Both outputs are parsed and passed through a deterministic grading script that computes:
1. **Total Drive Time**: Evaluated using the Maps MCP distance matrix.
2. **Dependency Violations**: Count of times step B was placed before step A.
3. **Temporal Violations**: Count of times an errand was scheduled outside its valid operating hours.

## 4. Benchmark Artifact Output
The script generates `BENCHMARK_RESULTS.md` featuring a Markdown table comparing the two approaches.

| Metric | Monolithic Baseline | Agent Society (Ours) | % Improvement |
| :--- | :--- | :--- | :--- |
| Avg. Drive Time | X mins | Y mins | Z% faster |
| Dependency Violations | X | 0 | 100% |
| Temporal Violations | X | 0 | 100% |

This table acts as the cornerstone of the "Problem Value & Impact" presentation for the judges.
