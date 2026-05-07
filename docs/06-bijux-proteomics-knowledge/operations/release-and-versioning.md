---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release notes should say when evidence semantics or review outputs changed
- persisted artifact changes need migration proof
- avoid mixing contradiction-model shifts with unrelated cleanup

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`
- `packages/bijux-proteomics-knowledge/tests`
