---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

Setup should get a reader to the package proof surface quickly instead of reproducing the whole repository in miniature.

## Operating Rules

- local setup should get you to planning, outcome, and repository proof quickly
- use fixtures that show realistic lab dependency and promotion cases
- keep recommendation-policy and runtime-infra setup outside the core lab review loop

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
