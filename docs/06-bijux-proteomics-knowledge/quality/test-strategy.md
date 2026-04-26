---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Test Strategy

A useful test strategy names what evidence is needed and why shallow coverage is not enough.

## Review Rules

- favor contradiction, confidence, and review-state tests over generic coverage claims
- cover persistence cases where knowledge meaning could drift silently
- use fixtures that show imperfect or conflicting evidence, not just ideal cases

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
