---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- do not treat this package as the preferred production deployment target when runtime already owns the surface
- deployment here is only justified when compatibility itself is being verified
- legacy deployment expectations should shrink over time, not expand

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `interfaces/http/app.py`
- `src/agentic_proteins/execution/`, `state/`, and `providers/`
- `packages/agentic-proteins/tests`
