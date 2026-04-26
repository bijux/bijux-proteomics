---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Recovery guidance should help maintainers restore the right behavior, not just any working state.

## Operating Rules

- recover by restoring correct knowledge meaning before adding convenience fallbacks
- separate contradiction-resolution bugs from storage failures
- treat silently misclassified evidence as a serious operational issue

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
