---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- guard the seams to evidence, contracts, and lab execution carefully
- avoid dependencies that turn the package into a hidden application layer
- prefer explicit inputs from neighbors over copied semantics

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
