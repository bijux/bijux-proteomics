---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Test Strategy

A useful test strategy names what evidence is needed and why shallow coverage is not enough.

## Review Rules

- favor tests that show why an outcome changed, not just that it changed
- cover ambiguity, contradiction, and decision-loop pressure cases
- treat report artifacts as quality surfaces, not optional extras

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
