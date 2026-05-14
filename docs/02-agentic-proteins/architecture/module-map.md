---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Module Map

`agentic-proteins` stays reviewable only when its structural families remain easy to name and defend. The package owns legacy compatibility forwarding, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/agentic_proteins/interfaces/` preserves CLI, HTTP, and
  structure-report entrypoints while pointing at canonical owners
- `src/agentic_proteins/agents/`, `execution/`, and `tools/` keep the
  remaining bridge-side orchestration and contract surfaces explicit
- `src/agentic_proteins/providers/` and `state/` hold provider selection and
  compatibility state seams that still need migration review

## First Proof Check

- `packages/agentic-proteins/src/agentic_proteins`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
