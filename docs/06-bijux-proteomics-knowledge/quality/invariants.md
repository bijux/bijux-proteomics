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

## Invariant Model

```mermaid
flowchart LR
    claims["claim and evidence meaning"]
    confidence["confidence and contradiction handling"]
    boundary["helpers do not redefine knowledge truth"]

    claims --> confidence --> boundary
```

This page should make knowledge invariants feel like truth-handling rules, not
just implementation habits. Reviewers should be able to see what has to stay
stable for downstream consumers to trust evidence and uncertainty together.

## Review Rules

- claim and evidence meaning remains canonical across consumers
- confidence and contradiction handling stay explicit enough to review
- repository and serialization helpers do not redefine knowledge truth

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`

## Design Pressure

Knowledge invariants weaken when contradiction handling or helper behavior can
quietly redefine what the package treats as truth. The package has to keep
meaning, uncertainty, and review surfaces visibly linked.
