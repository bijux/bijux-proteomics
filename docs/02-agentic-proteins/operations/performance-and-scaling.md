---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only when compatibility cost becomes operationally material
- avoid deep tuning that makes the bridge look like a permanent execution owner
- measure whether the real bottleneck belongs in the canonical runtime instead

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
