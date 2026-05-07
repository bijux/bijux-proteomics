---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- this package is primarily published lab logic rather than a standalone deployed runtime service
- deployment boundaries matter as lab artifact and repository boundaries
- service entrypoints that execute lab workflows belong elsewhere

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
