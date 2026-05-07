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

For `bijux-proteomics-knowledge`, done means evidence, contradiction, and confidence remain inspectable enough that downstream consumers are not forced to infer hidden truth.

## Completion Model

```mermaid
flowchart TB
    change["change lands in claims, evidence, confidence, or review"]
    meaning{"knowledge meaning still reviewable?"}
    proof{"contradiction and confidence proof updated?"}
    downstream{"stable interpretation path still visible?"}
    done["change is done"]

    change --> meaning
    meaning -->|yes| proof
    meaning -->|no| block1["not done"]
    proof -->|yes| downstream
    proof -->|no| block2["not done"]
    downstream -->|yes| done
    downstream -->|no| block3["not done"]
```

This page exists to keep storage edits from hiding semantic drift. The package is only done when a reviewer can still explain what is known, what conflicts, and what remains uncertain.

## Review Rules

- knowledge outputs remain at least as reviewable as before
- tests and docs still reveal contradiction and confidence behavior clearly
- downstream consumers receive a stable interpretation path

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`

## Design Pressure

The failure pattern here is false neatness: a change makes the stored shape simpler while making disagreement, uncertainty, or review posture harder to see.
