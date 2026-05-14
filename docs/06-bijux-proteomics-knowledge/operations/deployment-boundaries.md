---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- this package is primarily a published knowledge layer rather than a standalone deployed service
- deployment boundaries here are artifact and repository compatibility boundaries
- service concerns belong in runtime or application layers that transport the knowledge state

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/decision_briefs.py`
- `packages/bijux-proteomics-knowledge/tests`
