---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- `agentic_proteins` import paths that still exist for compatibility review
- `agentic_proteins.interfaces` and `api` for public entrypoints that forward toward the canonical runtime
- `agentic_proteins.execution`, `state`, and `report` only where callers still depend on those shapes

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/api/app.py`
- `packages/agentic-proteins/tests`
