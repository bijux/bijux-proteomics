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

- `agentic_proteins` root imports for the same top-level runtime exports that
  the canonical package exposes
- `agentic_proteins.interfaces` for public CLI, HTTP, and structure-report
  entrypoints that forward toward canonical owners
- `agentic_proteins.execution`, `state`, `providers`, `tools`, and `agents`
  only where callers still depend on those compatibility shapes

Public imports in this package are compatibility forwarding, not a second
runtime API. The [Compatibility Contract](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/compatibility-contract/)
defines the ceiling.

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/interfaces/http/app.py`
- `packages/agentic-proteins/tests`
