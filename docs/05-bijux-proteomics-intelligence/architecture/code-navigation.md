---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-intelligence` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics_intelligence/candidates.py` and `domain/candidates/` for decision inputs
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py` for scoring structure
- `src/bijux_proteomics_intelligence/report/`, `outcomes.py`, and `design_loop/` for explanation and control

## First Proof Check

- the source tree in `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
