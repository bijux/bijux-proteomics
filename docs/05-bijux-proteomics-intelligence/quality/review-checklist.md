---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

## Review Rules

- ask which decision lever actually changed
- check reports, briefs, and outcomes before trusting raw scores
- verify that evidence semantics remain owned by the knowledge layer

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
