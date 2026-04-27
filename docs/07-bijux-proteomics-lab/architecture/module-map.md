---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-proteomics-lab` stays reviewable only when its structural families remain easy to name and defend. The package owns lab-facing planning, outcome promotion, and assay-state handling, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py` own the lab-facing control flow
- `src/bijux_proteomics_lab/schema.py` and `serialization.py` own the lab contract boundary
- `src/bijux_proteomics_lab/repositories.py` owns durable storage seams for plans and outcomes

## First Proof Check

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
