---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- core is primarily a published contract layer, not an independently deployed runtime service
- deployment boundaries matter here as version and dependency boundaries
- operator-facing deployment concerns should stay in runtime or application layers

## First Proof Check

- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
- `packages/bijux-proteomics-core/tests`
