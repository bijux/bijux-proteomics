---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Review Checklist

A review checklist is useful only if it catches the real ways this package can drift.

For `bijux-proteomics-core`, the first review question is whether the change belongs in durable contract space at all. Core gets expensive fast when nearby runtime or policy concerns leak inward.

## Review Model

```mermaid
flowchart TB
    review["review proposed core change"]
    contract{"is this a durable core rule?"}
    alignment{"lifecycle, schema, and execution contract still agree?"}
    leakage{"runtime or intelligence concern leaking inward?"}
    approve["ready to approve"]

    review --> contract
    contract -->|yes| alignment
    contract -->|no| rehome["move to the owning package"]
    alignment -->|yes| leakage
    alignment -->|no| block1["keep reviewing"]
    leakage -->|no| approve
    leakage -->|yes| block2["keep reviewing"]
```

This is a boundary checklist before it is a style checklist. If the owning rule is ambiguous, every downstream package ends up compensating differently.

## Review Rules

- ask whether the change belongs in durable contract space
- verify lifecycle, schema, and execution-contract surfaces still agree
- check whether runtime or intelligence concerns are leaking inward

## First Proof Check

- `packages/bijux-proteomics-core/tests`
- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`

## Design Pressure

The failure here is approving a convenient local edit that turns one durable rule into several context-dependent interpretations.
