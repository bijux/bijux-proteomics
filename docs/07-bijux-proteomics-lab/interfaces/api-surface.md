---
title: Python API Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Python API surface

`bijux-proteomics-lab` is a typed Python library for operational laboratory
planning and evidence feedback. It has no standalone HTTP product and no
primary CLI. Runtime and application layers may transport lab contracts, but
lab owns their planning, readiness, outcome, and handoff meaning.

## Root planning API

```python
from bijux_proteomics_lab import (
    build_advisory_assay_plan,
    build_executable_assay_plan,
    plan_experiment_batches,
)
```

| Operation | Input | Output | Boundary |
| --- | --- | --- | --- |
| `build_advisory_assay_plan` | governed program and optional evidence bundle | open gaps, assay recommendations, wet-lab actions | explicitly non-executable |
| `plan_experiment_batches` | program, optional evidence, optional assay dependencies | prioritized batches, review queue, evidence gaps | does not confirm inventory, reagents, or success likelihood |
| `build_executable_assay_plan` | experiment plan, selected batch, declared sample kinds | instructions, blockers, readiness flag | structural readiness does not guarantee assay performance |

The root API budget is three symbols. Models and secondary operations stay in
their owner modules so package-root convenience cannot erase the difference
between advice, design, readiness, execution, and observed outcome.

## Executable-plan example

```python
from bijux_proteomics_lab import build_executable_assay_plan
from bijux_proteomics_lab.planning import ExperimentBatch, ExperimentPlan

plan = ExperimentPlan(
    program_id="prog-demonstration",
    batches=[
        ExperimentBatch(
            batch_id="batch-qc",
            objective="Verify measurement readiness",
            assay_ids=["assay-system-suitability"],
            priority=1,
            sample_requirements=["reference-plasma"],
            assay_sample_kinds={
                "assay-system-suitability": "reference-plasma",
            },
        )
    ],
)

executable = build_executable_assay_plan(
    plan,
    batch_id="batch-qc",
    available_sample_kinds=["reference-plasma"],
)

assert executable.ready_for_execution is True
assert executable.blocked_by == []
```

If the sample kind is absent or a blocking review gate remains, the same call
returns instructions together with explicit `blocked_by` reasons and
`ready_for_execution=False`. An unknown batch ID raises `ValueError`.

## Owner bands

| Import band | Representative contracts |
| --- | --- |
| `planning` | assay plans, dependencies, batches, schedules, capacity, materials, queues, next-cycle recommendations |
| `design` | experimental-design validation, power advice, randomization, fractions, multiplexing, QC samples, carryover |
| `readiness` | workflow-stage and live operational-readiness reports |
| `handoffs` | risk assessments, explanations, authority boundaries, refusals, artifact registries, LIMS exports, PTM packets, targeted reviews, QC feedback |
| `outcomes` | assay definitions and observations, acceptance, failure triage, reliability, rerun, evidence promotion, feedback records |
| `lifecycle` | review queue, promotion, assay stage, and candidate advancement transitions |
| `reconciliation` | follow-up interpretation and flagship reconciliation |
| `benchmarks` | claim tests, follow-up evidence, learning loops, rehearsals, and outcome dossiers |

## Outcome semantics

Outcomes distinguish completion state, QC state, failure class, acceptance rule,
reliability, rerun policy, and evidence-promotion readiness. Promotion functions
do not merely convert every observation into knowledge; they evaluate governed
conditions and retain why evidence was or was not promotable.

## Failure and refusal behavior

- Validation errors reject malformed plans, instructions, observations, and
  lifecycle transitions.
- Dependency reports preserve unknown assays, self-dependencies, and cycles.
- Readiness reports retain missing materials, controls, lineage, evidence,
  staffing, budget, capacity, and backlog pressure.
- Handoff refusal is a valid safety result when support or authority is
  insufficient.
- Technical failure, biological failure, inconclusive measurement, and policy
  refusal remain distinguishable.

See [Data contracts](data-contracts.md) for state meanings and
[Artifact contracts](artifact-contracts.md) for portable handoff requirements.
