---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics_foundation.identity` and `serialization` for shared identifiers and payload meaning
- `bijux_proteomics_foundation.serialization` for durable transport shapes
- `bijux_proteomics_foundation.compatibility` and `outcomes` for compatibility and failure vocabulary

## First Proof Check

- `src/bijux_proteomics_foundation/identity/identifiers.py` and `serialization/document_schema.py`
- `src/bijux_proteomics_foundation/serialization/` and `compatibility/schema_migrations.py`
- `packages/bijux-proteomics-foundation/tests`
