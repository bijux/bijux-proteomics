---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security posture includes resisting opaque decision behavior
- treat unreviewable policy overrides as operational risk
- keep provider, secret, and runtime concerns outside the package unless the output contract truly depends on them

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
