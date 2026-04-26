---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

## Review Rules

- ask whether the change affects evidence meaning, review meaning, or only storage shape
- check contradiction and confidence examples before approving
- verify that downstream convenience is not rewriting canonical truth

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
