---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

Lab scale is constrained by two systems at once: computational planning and physical execution. Faster plan generation does not increase useful throughput when instruments, material, controls, staff, or review capacity are the limiting resource.

## Capacity model

| Dimension | Planning representation | Operational consequence |
| --- | --- | --- |
| assay dependencies | dependency graph and critical path | work cannot start before prerequisite evidence or assays complete |
| instrument availability | instrument and family capacity | batches queue or move to another feasible window |
| samples and reagents | material requirements, inventory, and reservations | scarce or expired material blocks execution |
| staffing | role and availability signals | preparation, operation, or review becomes the bottleneck |
| controls | protocol requirements and readiness signals | missing positive, negative, spike-in, or process controls can force refusal |
| review backlog | queue pressure and service expectations | completed data may wait before disposition or promotion |
| reruns | failure class and rerun policy | capacity is consumed again and downstream timelines change |
| handoff formats | records, mappings, and field loss | delivery volume raises validation and reconciliation burden |

## Computational scaling

Dependency ordering, cycle detection, critical-path analysis, candidate priority, schedule scenarios, readiness evaluation, artifact rendering, outcome summaries, and feedback queries are local typed operations. Runtime may parallelize independent plans or scenarios, but the merge must retain deterministic identifiers, ordering, and constraint decisions.

Do not split an experiment in a way that breaks randomization, blocking, multiplex balance, shared controls, batch correction, or acceptance scope. A smaller computational unit is unsafe when it changes the design being evaluated.

## Operational throughput

Measure flow across the entire loop:

- proposed, advisory, executable, refused, scheduled, and completed assay counts;
- wait time by dependency, material, instrument, staffing, and review cause;
- utilization by assay family and instrument;
- control-readiness and provenance-readiness failure rates;
- handoff rejection, mapping-loss, duplicate-delivery, and acknowledgement rates;
- QC caution and failure rates, rerun frequency, and time to disposition;
- planned-versus-observed deltas and feedback-cycle latency;
- evidence promotions that survive downstream review.

High utilization is not a success metric by itself. A saturated instrument producing weakly controlled or repeatedly failed runs is operational debt, not scale.

## Performance evidence

The package has constrained-capacity, insufficient-material, contradictory-readiness, scheduling, queue, benchmark-rehearsal, and outcome-dossier fixtures. These validate operational decisions and failure behavior. It does not currently publish a dedicated computational performance suite or a laboratory throughput SLA.

Run the relevant behavioral evidence:

```bash
python -m pytest \
  packages/bijux-proteomics-lab/tests/planning \
  packages/bijux-proteomics-lab/tests/readiness \
  packages/bijux-proteomics-lab/tests/handoffs \
  packages/bijux-proteomics-lab/tests/outcomes
```

Scale by making constraints visible earlier, comparing schedule scenarios, reserving scarce material intentionally, and closing the outcome loop. Never increase reported throughput by dropping blocked work, partial observations, failed controls, or reruns from the denominator.
