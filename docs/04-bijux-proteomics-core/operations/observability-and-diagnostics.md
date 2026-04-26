---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- diagnostics should expose contract, lifecycle, and readiness failures cleanly
- tests and CLI output are often the primary observability surface for this package
- make it easy to see whether a failure is semantic or integration-related

## First Proof Check

- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
- `packages/bijux-proteomics-core/tests`
