---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- guard the line between lab records and upstream recommendation logic
- keep shared contracts in foundation and core rather than copying them locally
- avoid dependencies that make repository helpers the hidden owner of behavior

## First Proof Check

- `packages/bijux-proteomics-lab/tests`
- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/repositories.py` and `serialization.py`
