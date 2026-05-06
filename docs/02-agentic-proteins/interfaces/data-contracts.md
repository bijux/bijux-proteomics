---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts are the quickest way to judge whether a package really owns a concept or is just passing it through.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- legacy request and response payloads
- state, memory, and execution schemas still consumed by callers
- public shapes that must remain traceable to the canonical runtime model

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/interfaces/http/app.py`
- `packages/agentic-proteins/tests`
