---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Invariants

Invariants are the claims that must remain true for the package to stay worth trusting.

## Review Rules

- shared identifiers and schema meanings remain canonical across consuming packages
- serialization and migration paths stay explicit and reviewable
- foundation never absorbs downstream policy just because many packages use it

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
