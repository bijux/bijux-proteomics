---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

For `bijux-proteomics-lab`, review has to separate workflow convenience from durable operator truth. A fast lab-facing change is still wrong if the record becomes harder to reconstruct.

## Review Model

```mermaid
flowchart TB
    review["review proposed lab change"]
    layer{"planning meaning, outcome meaning, or storage detail?"}
    proof{"promotion and prerequisite cases still defended?"}
    record{"durable record still aligns with shared contracts?"}
    approve["ready to approve"]

    review --> layer
    layer --> proof
    proof -->|yes| record
    proof -->|no| block1["keep reviewing"]
    record -->|yes| approve
    record -->|no| block2["keep reviewing"]
```

This checklist is useful only if it catches when operator-facing clarity is being traded away for implementation convenience.

## Review Rules

- ask whether the change alters planning meaning, outcome meaning, or only storage detail
- check promotion and prerequisite examples before approval
- verify that durable records still align with shared contracts

## First Proof Check

- `packages/bijux-proteomics-lab/tests`
- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`

## Design Pressure

The easy mistake is to approve a change because the assay loop still runs, while the planning history or promotion path has become harder to explain after the fact.
