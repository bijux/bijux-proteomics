---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `agentic-proteins` is by private memory, the docs are not doing enough.

## Start Here

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py` for entrypoint ownership
- `src/agentic_proteins/runtime/workspace.py` and `core/execution.py` for runtime translation
- `packages/agentic-proteins/tests` for compatibility proof and retirement pressure

## First Proof Check

- the source tree in `packages/agentic-proteins/src/agentic_proteins`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
