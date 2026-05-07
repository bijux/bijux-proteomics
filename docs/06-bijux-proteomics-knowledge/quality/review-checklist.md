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

For `bijux-proteomics-knowledge`, review should distinguish semantic change from storage change before any confidence comes from green checks.

## Review Model

```mermaid
flowchart TB
    review["review proposed knowledge change"]
    layer{"truth, review state, or storage detail?"}
    examples{"contradiction and confidence examples still honest?"}
    convenience{"downstream convenience rewriting canonical truth?"}
    approve["ready to approve"]

    review --> layer
    layer --> examples
    examples -->|yes| convenience
    examples -->|no| block1["keep reviewing"]
    convenience -->|no| approve
    convenience -->|yes| block2["keep reviewing"]
```

The checklist exists so a cleaner persistence shape does not get mistaken for a safer truth model.

## Review Rules

- ask whether the change affects evidence meaning, review meaning, or only storage shape
- check contradiction and confidence examples before approving
- verify that downstream convenience is not rewriting canonical truth

## First Proof Check

- `packages/bijux-proteomics-knowledge/tests`
- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`

## Design Pressure

The common drift is to approve a storage or ergonomics change that quietly changes what downstream systems are allowed to believe.
