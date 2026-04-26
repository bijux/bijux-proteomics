---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-proteomics-intelligence` stays reviewable only when its structural families remain easy to name and defend. The package owns candidate evaluation, decision policy, and explainable recommendation flow, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/bijux_proteomics_intelligence/candidates.py` and `domain/candidates/` own candidate state and portfolio structure
- `src/bijux_proteomics_intelligence/policies.py`, `evaluators.py`, and `domain/metrics/` own scoring and decision rules
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, `outcomes.py`, and `design_loop/` own explainability and control-loop structure

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
