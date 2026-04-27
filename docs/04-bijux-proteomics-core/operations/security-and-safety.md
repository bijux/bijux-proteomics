---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security fixes should preserve explicit validation and contract boundaries
- unsafe coercion or implicit defaults are operational and security risks here
- do not hide sensitive execution assumptions inside generic core helpers

## First Proof Check

- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
- `packages/bijux-proteomics-core/tests`
