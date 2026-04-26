---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- keep dependencies minimal and shared-purpose
- do not add package-specific policy dependencies to foundation
- prefer versioned adapters over hidden dependency magic

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
