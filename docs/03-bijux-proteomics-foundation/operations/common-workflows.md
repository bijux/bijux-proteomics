---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- validate a shared type change against all consuming package expectations
- review serialization and migration output before calling the change safe
- update package-facing docs when shared meaning changes

## First Proof Check

- `src/bijux_proteomics_foundation/documents.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
