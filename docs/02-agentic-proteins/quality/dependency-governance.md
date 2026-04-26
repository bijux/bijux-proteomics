---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- new dependencies need migration or compatibility justification
- avoid binding modern packages more tightly to the legacy bridge
- prefer runtime-owned solutions when a new dependency is really about execution

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/`
