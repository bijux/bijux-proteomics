---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- review outputs and serialized records are the main diagnostics
- make contradictions, confidence shifts, and review decisions easy to inspect
- track which schema or rule version produced a disputed record

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
