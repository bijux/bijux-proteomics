---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release review must include downstream compatibility thinking
- schema shifts require visible migration notes and test proof
- shared-version movement should be rarer and more deliberate than workflow releases elsewhere

## First Proof Check

- `src/bijux_proteomics_foundation/serialization/document_schema.py` and `compatibility/schema_migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
