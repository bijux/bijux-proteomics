---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- verify a legacy import, CLI, or API path still reaches the intended runtime behavior
- document whether the change preserves, narrows, or retires a compatibility promise
- update migration-facing docs when a legacy path becomes easier to remove

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
