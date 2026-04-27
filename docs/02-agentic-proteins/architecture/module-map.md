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

- `src/agentic_proteins/interfaces/`, `api/`, and `runtime/` translate public legacy entrypoints into the canonical runtime path
- `src/agentic_proteins/core/`, `execution/`, and `validation/` preserve legacy control semantics that still need explicit migration review
- `src/agentic_proteins/providers/`, `memory/`, `state/`, and `report/` hold adapter and artifact seams that must not outgrow the bridge role

## First Proof Check

- `packages/agentic-proteins/src/agentic_proteins`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
