---
title: Entrypoints and Worked Examples
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Entrypoints and worked examples

The package root intentionally exposes only three planning operations:
`build_advisory_assay_plan`, `plan_experiment_batches`, and
`build_executable_assay_plan`. Design, readiness, handoff, outcomes, lifecycle,
and reconciliation remain in named owner modules. Lab has no standalone CLI or
HTTP API.

## Produce scientific advice

```python
from bijux_proteomics_lab import build_advisory_assay_plan

# `program` is a governed ProgramSpec from bijux-proteomics-core.
# `evidence` is an optional EvidenceBundle from bijux-proteomics-knowledge.
advisory = build_advisory_assay_plan(program, evidence)

assert advisory.executable is False
for recommendation in advisory.recommendations:
    print(recommendation.assay_id, recommendation.blocking)
    print(*recommendation.rationale, sep="\n  - ")
```

This output prioritizes scientific follow-up. It cannot be handed directly to
an operator as a run instruction.

## Create and review batches

```python
from bijux_proteomics_lab import plan_experiment_batches
from bijux_proteomics_lab.planning.assays import AssayDependency

plan = plan_experiment_batches(
    program,
    evidence,
    dependencies=[
        AssayDependency(
            assay_id="assay:cellular-response",
            requires_assay_id="assay:binding",
        )
    ],
)

for batch in plan.batches:
    print(batch.batch_id, batch.priority, batch.sample_requirements)
```

Dependency errors are not reordered heuristically. Resolve missing assays and
cycles before scheduling or execution review.

## Materialize one executable batch

```python
from bijux_proteomics_lab import build_executable_assay_plan

batch = plan.batches[0]
executable = build_executable_assay_plan(
    plan,
    batch_id=batch.batch_id,
    available_sample_kinds=list(batch.sample_requirements),
)

print(executable.ready_for_execution)
for blocker in executable.blocked_by:
    print("BLOCKED:", blocker)
for instruction in executable.instructions:
    print(instruction.instruction_id, instruction.preflight_checks)
```

Supplying sample kinds clears only inventory declarations. Blocking review gates
remain in `blocked_by` until a governed review process clears them; do not edit
the returned model to simulate approval.

## Choose the next surface

- `design` owns experimental structure, protocols, controls, randomization,
  multiplexing, fractionation, power advice, and carryover risk.
- `readiness` owns material, reagent, staff, instrument, control, evidence, and
  provenance readiness.
- `planning` owns priorities, capacity schedules, queues, burden, information
  gain, and next-cycle assays.
- `handoffs` owns explanations, refusals, canonical envelopes, LIMS exports,
  PTM packets, risk, and QC feedback.
- `outcomes` owns observations, result states, evidence promotion, and feedback.
- `reconciliation` owns planned-versus-observed deltas and operational follow-up.
- `lifecycle` owns reviewed progression and promotion transitions.

Persist the advisory plan, reviewed executable plan, observed outcome, and
reconciliation as separate linked artifacts.
