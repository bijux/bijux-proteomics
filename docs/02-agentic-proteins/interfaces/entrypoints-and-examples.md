---
title: Entrypoints and Examples
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Entrypoints and Examples

Examples should route readers into the real surface quickly and avoid making side paths look canonical.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- show the legacy path only when it is the migration subject
- pair every bridge example with the canonical runtime destination
- avoid examples that make the bridge look like the strategic surface

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/api/app.py`
- `packages/agentic-proteins/tests`
