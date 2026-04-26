---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# API Surface

An API surface is only real when the package actually owns the network-facing contract, not when docs are trying to look complete.

## Package Surface

- `src/agentic_proteins/api/app.py` is the legacy HTTP entry surface that should stay compatible while migration remains open
- new network behavior should land in `bijux-proteomics-runtime` unless the bridge is the specific subject of review
- API changes here require explicit migration and retirement reasoning

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/api/app.py`
- `packages/agentic-proteins/tests`
