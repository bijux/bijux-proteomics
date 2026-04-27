---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration belongs in the public surface only when a reader must understand it to use the package safely.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- provider selection and runtime controls
- workspace and persistence settings
- compatibility toggles required to preserve a legacy path during migration

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/api/app.py`
- `packages/agentic-proteins/tests`
