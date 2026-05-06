---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-proteomics-foundation` stays reviewable only when its structural families remain easy to name and defend. The package owns shared identifiers, schema meaning, and serialization compatibility, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/bijux_proteomics_foundation/identity/identifiers.py` and `serialization/document_schema.py` define stable shared identifiers and payload shape
- `src/bijux_proteomics_foundation/serialization/` and `compatibility/schema_migrations.py` own durable transport and version movement
- `src/bijux_proteomics_foundation/outcomes/` keeps shared failure vocabulary small and reusable

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
