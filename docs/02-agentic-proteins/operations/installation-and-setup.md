---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

Setup should get a reader to the package proof surface quickly instead of reproducing the whole repository in miniature.

## Operating Rules

- treat local setup as a compatibility test bed, not the strategic runtime environment
- install and run only the surfaces needed to prove an existing legacy path still forwards correctly
- pair local setup with the runtime handbook when a surface is being migrated away

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
