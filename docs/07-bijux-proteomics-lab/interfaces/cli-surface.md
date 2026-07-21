---
title: Library and Execution Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Library and execution boundaries

`bijux-proteomics-lab` installs no command-line executable and does not control
laboratory instruments. Its public contract is a typed Python planning and
handoff library. The package can determine that a plan is structurally ready;
it cannot confirm that a person, instrument, reagent, LIMS, or facility is
actually ready unless those facts are supplied through the relevant contracts.

The package root intentionally exposes only three operations:

```python
from bijux_proteomics_lab import (
    build_advisory_assay_plan,
    build_executable_assay_plan,
    plan_experiment_batches,
)
```

This narrow facade preserves an important distinction:

- an advisory plan says which experiment could reduce uncertainty;
- an experiment plan groups and orders required work;
- an executable plan contains reviewed instructions and explicit blockers;
- a laboratory execution request authorizes a handoff;
- an observed outcome records what happened;
- evidence promotion decides what the outcome is allowed to support.

## Integrate with an operational system

| Concern | Owning surface |
| --- | --- |
| Scientific assay priority and design | Lab planning and design contracts |
| Material, control, staffing, capacity, and lineage readiness | Lab readiness reports |
| Instrument submission and process supervision | Facility or instrument-control system |
| LIMS field mapping and acknowledged loss | Lab handoff export contracts |
| Runtime computation and artifacts | `bijux-proteomics-runtime` |
| Durable evidence and claim state | `bijux-proteomics-knowledge` after promotion |

A CLI, service, scheduler, or LIMS adapter may transport these models, but it
must preserve `ready_for_execution`, `blocked_by`, review authority, preflight
checks, sample lineage, control requirements, and artifact fingerprints.
Successful serialization is not execution authorization.

Use [Python API surface](api-surface.md) for the owner-module map and
[Entrypoints and worked examples](entrypoints-and-examples.md) for the complete
advisory-to-executable transition.
