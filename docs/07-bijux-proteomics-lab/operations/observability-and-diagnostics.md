---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- plan, outcome, and repository records are the main diagnostics
- make missing prerequisites and promotion reasons easy to inspect
- observe which upstream recommendation or shared contract drove a lab record

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
