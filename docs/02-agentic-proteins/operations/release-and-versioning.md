---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- every release question should ask whether a compatibility promise can be narrowed or removed
- document breaking changes against the migration ledger, not just local version numbers
- avoid shipping new surface area under the cover of maintenance releases

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
