---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only after proving evaluator or report cost is a real bottleneck
- do not trade explainability for speed
- if a performance fix weakens reviewability, it belongs in a different design

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
