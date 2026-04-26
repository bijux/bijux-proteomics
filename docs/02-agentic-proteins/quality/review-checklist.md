---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

## Review Rules

- ask whether the change shrinks or expands legacy surface area
- check whether runtime already owns the better place for the behavior
- verify that public docs and tests still agree on the compatibility promise

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/`
