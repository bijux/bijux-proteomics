---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Definition of Done

Done means the package is easier to trust after the change, not just that the diff merged.

## Review Rules

- operators can still explain what happened from the durable record
- tests and docs defend the changed lab surface clearly
- upstream and downstream consumers still align on the payload meaning

## First Proof Check

- `packages/bijux-proteomics-lab/tests`
- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/repositories.py` and `serialization.py`
