---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration belongs in the public surface only when a reader must understand it to use the package safely.

## Package Surface

- schema-version and migration choices
- serialization format expectations
- compatibility defaults that downstream packages must review explicitly

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py`
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
