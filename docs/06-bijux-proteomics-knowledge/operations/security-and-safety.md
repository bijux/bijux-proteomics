---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security here includes protecting the integrity of evidence interpretation
- malformed or contradictory inputs should fail visibly
- keep runtime credentials and operator concerns outside the knowledge layer

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
