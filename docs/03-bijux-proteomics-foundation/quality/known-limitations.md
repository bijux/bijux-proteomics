---
title: Known Limitations
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Known Limitations

Known limitations matter because honest boundaries are part of quality, not an admission of failure.

## Review Rules

- foundation cannot prove downstream usage by itself
- shared types still depend on consuming packages to honor them correctly
- versioning discipline is only as strong as the migration tests that enforce it

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
