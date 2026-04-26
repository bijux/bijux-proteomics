---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Definition of Done

Done means the package is easier to trust after the change, not just that the diff merged.

## Review Rules

- knowledge outputs remain at least as reviewable as before
- tests and docs still reveal contradiction and confidence behavior clearly
- downstream consumers receive a stable interpretation path

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
