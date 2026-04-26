---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Definition of Done

Done means the package is easier to trust after the change, not just that the diff merged.

## Review Rules

- the changed recommendation path is easier to justify than before
- tests and docs explain the outcome shift in reader language
- downstream consumers can still interpret outputs safely

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
