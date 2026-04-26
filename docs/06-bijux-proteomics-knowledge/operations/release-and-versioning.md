---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release notes should say when evidence semantics or review outputs changed
- persisted artifact changes need migration proof
- avoid mixing contradiction-model shifts with unrelated cleanup

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
