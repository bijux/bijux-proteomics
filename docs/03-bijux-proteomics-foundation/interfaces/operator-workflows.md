---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Operator workflows should say who uses the surface, why they use it, and when they should stop and open a neighbor handbook instead.

## Package Surface

- package authors reviewing a shared type change
- maintainers validating serialization compatibility
- migration reviewers checking whether a new version path is defensible

## First Proof Check

- `src/bijux_proteomics_foundation/identity/identifiers.py` and `documents.py`
- `src/bijux_proteomics_foundation/serialization/` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
