---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only when planning or repository cost is actually limiting work
- do not hide lab-state transitions behind clever fast paths
- shared or runtime-level bottlenecks belong with their real owner

## First Proof Check

- `src/bijux_proteomics_lab/benchmarks/rehearsals.py` and `planning/assays.py`
- `src/bijux_proteomics_lab/outcomes/observations.py` and `repositories.py`
- `packages/bijux-proteomics-lab/tests`
