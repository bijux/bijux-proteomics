---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- this package does not own a standalone CLI product surface
- command-line workflows belong in consuming packages or maintainer tooling
- if a CLI seems necessary here, the request is usually for validation helpers or examples instead

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py`
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
