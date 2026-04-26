---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- `src/agentic_proteins/interfaces/cli.py` is a compatibility CLI surface, not the preferred long-term operator surface
- new CLI affordances belong in the canonical runtime unless needed to preserve an existing contract
- CLI output drift should be treated as migration-sensitive behavior

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/api/app.py`
- `packages/agentic-proteins/tests`
