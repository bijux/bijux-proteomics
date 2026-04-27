---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Artifacts matter because they survive the moment of execution and become someone else's input or evidence.

## Package Surface

- serialized payloads that move between packages or persist across versions
- migration-aware schema forms
- shared error and compatibility records that consuming packages can reuse

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py`
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
