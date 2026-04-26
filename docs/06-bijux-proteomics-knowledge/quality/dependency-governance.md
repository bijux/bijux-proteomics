---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency governance is really boundary governance under another name.

## Review Rules

- guard the line between knowledge meaning and downstream decision policy
- keep runtime and storage dependencies from becoming semantic owners
- prefer explicit repository and schema boundaries over hidden shared state

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
