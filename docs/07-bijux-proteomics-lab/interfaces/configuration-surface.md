---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration belongs in the public surface only when a reader must understand it to use the package safely.

## Package Surface

- planning and outcome handling choices that remain visible in lab state
- repository expectations for durable lab records
- serialization settings needed to keep lab payloads stable

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py`
- `packages/bijux-proteomics-lab/tests`
