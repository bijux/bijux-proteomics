---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-foundation` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics_foundation/ids.py` and `schema.py` for shared meaning
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py` for compatibility movement
- `packages/bijux-proteomics-foundation/tests` for cross-package proof

## First Proof Check

- the source tree in `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
