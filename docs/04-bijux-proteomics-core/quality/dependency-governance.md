---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- guard the boundary between shared foundation dependencies and downstream policy consumers
- keep runtime interaction behind explicit seams
- avoid dependencies that make core a transit point for unrelated concerns

## First Proof Check

- `packages/bijux-proteomics-core/tests`
- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
