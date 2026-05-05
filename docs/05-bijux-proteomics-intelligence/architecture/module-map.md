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

- `src/bijux_proteomics_intelligence/candidates/` owns candidate records, ranking, lifecycle, quality, and validation
- `src/bijux_proteomics_intelligence/judgment/` and `posture/` own scoring, recommendation, refusal, and skeptical challenge rules
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/` own review projection, interpretation contracts, and refinement structure

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
