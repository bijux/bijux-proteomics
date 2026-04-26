---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

## Review Rules

- ask whether the change belongs in durable contract space
- verify lifecycle, schema, and execution-contract surfaces still agree
- check whether runtime or intelligence concerns are leaking inward

## First Proof Check

- `packages/bijux-proteomics-core/tests`
- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
