---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Definition of Done

Done means the package is easier to trust after the change, not just that the diff merged.

## Review Rules

- shared meaning is still clearer after the change than before it
- migration and serialization proof cover the edited surface
- downstream packages have an explicit path to remain compatible

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
