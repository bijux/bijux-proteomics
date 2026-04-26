---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security work should preserve the integrity of plan and outcome records
- invalid upstream inputs should fail visibly at the lab boundary
- keep generic secret, provider, and runtime control concerns outside this package

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/repositories.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
