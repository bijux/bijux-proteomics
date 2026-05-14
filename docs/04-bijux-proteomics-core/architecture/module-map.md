---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-proteomics-core` stays reviewable only when its structural families remain easy to name and defend. The package owns durable program contracts and biological domain primitives, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py` own durable program contracts
- `src/bijux_proteomics/domain/lifecycle.py`, `domain/validation.py`, `execution/backend.py`, and `domain/constraints.py` own readiness and execution rules
- `src/bijux_proteomics/biology/`, `domain/`, and `execution/` hold domain primitives and structural seams to neighboring packages

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
