---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts are the quickest way to judge whether a package really owns a concept or is just passing it through.

## Package Surface

- canonical identifiers
- shared payload shapes and validation rules
- migration contracts that keep versions legible across package boundaries

## First Proof Check

- `src/bijux_proteomics_foundation/identity/identifiers.py` and `documents.py`
- `src/bijux_proteomics_foundation/serialization/` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
