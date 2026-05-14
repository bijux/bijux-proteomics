---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only where contract validation or core transforms are demonstrably hot
- do not blur durable semantics for speed
- runtime-level tuning belongs in runtime unless the contract layer itself is slow

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`
