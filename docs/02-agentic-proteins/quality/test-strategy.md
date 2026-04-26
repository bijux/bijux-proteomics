---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Test Strategy

A useful test strategy names what evidence is needed and why shallow coverage is not enough.

## Review Rules

- favor compatibility tests that compare the bridge path to the canonical runtime result
- cover retirement-sensitive CLI, API, and import surfaces explicitly
- do not let shallow smoke tests substitute for migration proof

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/`
