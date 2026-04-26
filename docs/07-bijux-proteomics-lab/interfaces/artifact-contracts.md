---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Artifacts matter because they survive the moment of execution and become someone else's input or evidence.

## Package Surface

- assay plans and schedule-oriented payloads
- lab outcome and promotion records
- serialized representations used to persist or move lab state

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/schema.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
