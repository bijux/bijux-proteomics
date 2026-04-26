---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- reports, briefs, and outcome payloads are core diagnostics here
- observe which metric or policy change moved the recommendation
- make uncertainty and contradiction visible rather than smoothing them away

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
