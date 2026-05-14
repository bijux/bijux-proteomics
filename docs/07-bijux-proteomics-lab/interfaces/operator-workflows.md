---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Operator workflows should say who uses the surface, why they use it, and when they should stop and open a neighbor handbook instead.

## Package Surface

- operators reviewing assay planning or promoted outcomes
- developers adjusting lab payloads without breaking downstream consumers
- maintainers validating that lab records still line up with shared contracts

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py`
- `packages/bijux-proteomics-lab/tests`
