---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development guidance should protect package boundaries while making routine edits easier to review.

## Operating Rules

- change one shared meaning at a time and review the downstream blast radius immediately
- run migration and serialization proof whenever a schema-facing edit lands
- treat convenience coercion as a red flag during local development

## First Proof Check

- `src/bijux_proteomics_foundation/serialization/documents.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
