---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics_lab.planning` and `outcomes` for lab control surfaces
- `bijux_proteomics_lab.schema` and `serialization` for stable lab payloads
- `bijux_proteomics_lab.repositories` for durable plan and outcome records

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py`
- `packages/bijux-proteomics-lab/tests`
