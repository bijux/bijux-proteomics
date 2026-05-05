---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security work should preserve shared validation strictness
- malformed payload handling belongs in explicit schema and migration rules
- avoid embedding package-specific credential or provider concerns into foundation

## First Proof Check

- `src/bijux_proteomics_foundation/serialization/documents.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
