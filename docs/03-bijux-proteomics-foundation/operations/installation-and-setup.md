---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

Setup should get a reader to the package proof surface quickly instead of reproducing the whole repository in miniature.

## Operating Rules

- local setup should emphasize schema validation and migration review rather than service bootstrapping
- use examples and tests that show shared types behaving the same way across package boundaries
- keep setup light enough that foundation remains easy for every package owner to validate

## First Proof Check

- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
- `packages/bijux-proteomics-foundation/tests`
