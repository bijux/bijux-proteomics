---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- this package is primarily published decision logic, not an independently deployed runtime service
- deployment boundaries matter as output-contract boundaries for downstream consumers
- operator-facing runtime surfaces belong elsewhere even when they execute intelligence behavior

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
