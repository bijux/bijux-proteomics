---
title: Risk Register
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Risk Register

A risk register should name the structural and behavioral failures that deserve ongoing attention.

## Review Rules

- policy drift becomes opaque
- new metrics land without enough reviewable explanation
- recommendation logic starts absorbing lab or runtime concerns

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
