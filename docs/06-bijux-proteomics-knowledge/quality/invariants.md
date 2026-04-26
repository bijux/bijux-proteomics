---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Invariants

Invariants are the claims that must remain true for the package to stay worth trusting.

## Review Rules

- claim and evidence meaning remains canonical across consumers
- confidence and contradiction handling stay explicit enough to review
- repository and serialization helpers do not redefine knowledge truth

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
