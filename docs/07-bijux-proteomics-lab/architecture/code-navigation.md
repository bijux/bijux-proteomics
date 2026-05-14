---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-lab` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py` for lab control flow
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py` for contract boundaries
- `packages/bijux-proteomics-lab/tests` for planning and promotion proof

## First Proof Check

- the source tree in `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
