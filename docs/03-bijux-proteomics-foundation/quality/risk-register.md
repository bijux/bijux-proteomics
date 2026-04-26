---
title: Risk Register
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Risk Register

A risk register should name the structural and behavioral failures that deserve ongoing attention.

## Review Rules

- shared types start carrying policy that belongs elsewhere
- migration promises drift from actual serialized payloads
- consuming packages fork the meaning in practice

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
