---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility commitments are expensive promises. They should be visible enough that nobody expands them by accident.

## Package Surface

- treat foundation types as cross-package contracts, not local implementation detail
- version movement must be explicit and reviewable
- shared meanings should change slower than downstream workflow code

## First Proof Check

- `src/bijux_proteomics_foundation/identity/identifiers.py` and `documents.py`
- `src/bijux_proteomics_foundation/serialization/` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
