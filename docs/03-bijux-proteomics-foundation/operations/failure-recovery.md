---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Recovery guidance should help maintainers restore the right behavior, not just any working state.

## Operating Rules

- recover from breakage by restoring canonical shared meaning, not by adding permissive exceptions
- revert or version bad migrations explicitly
- check consuming packages for downstream fallout before calling recovery complete

## First Proof Check

- `src/bijux_proteomics_foundation/serialization/document_schema.py` and `compatibility/schema_migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
