---
title: Change Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Change Validation

Change validation should make it obvious whether a package edit is safe, risky, or mis-scoped.

## Review Rules

- require proof when evidence meaning, review state, or persisted artifacts change
- run contradiction and repository checks together when durable state moves
- reject edits that make uncertainty easier to ignore

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
