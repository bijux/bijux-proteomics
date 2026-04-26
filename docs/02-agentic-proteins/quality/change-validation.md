---
title: Change Validation
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Change Validation

Change validation should make it obvious whether a package edit is safe, risky, or mis-scoped.

## Review Rules

- every change should say whether it preserves, narrows, or retires a compatibility promise
- run the closest bridge-to-runtime proof before accepting the edit
- treat unexplained divergence from runtime as a failed validation

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/`
