---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics_intelligence.candidates`, `policies`, and `evaluators` for decision logic imports
- `bijux_proteomics_intelligence.report` and `briefs` for explainability surfaces
- `bijux_proteomics_intelligence.outcomes` and `serialization` for durable decision outputs

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates.py`, `policies.py`, and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
