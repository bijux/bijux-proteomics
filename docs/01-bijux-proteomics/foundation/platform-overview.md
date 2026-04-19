---
title: Platform Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Platform Overview

`bijux-proteomics` is a multi-package system because protein-program design is
easier to trust when runtime control, shared primitives, domain contracts,
decision logic, evidence handling, and lab execution stay distinct.

Read the platform as a chain of responsibilities rather than as a directory
list. Foundation stabilizes shared payload meaning. Core defines program and
lifecycle contracts. Knowledge tracks evidence and claims. Intelligence turns
those inputs into inspectable decisions. Lab turns decisions into assay work.
`agentic-proteins` governs execution, replay, and final runtime behavior.

```mermaid
flowchart LR
    foundation[bijux-proteomics-foundation\nshared primitives]
    core[bijux-proteomics-core\nprogram contracts]
    knowledge[bijux-proteomics-knowledge\nevidence + claims]
    intelligence[bijux-proteomics-intelligence\ndecision support]
    lab[bijux-proteomics-lab\nassay execution]
    agentic[agentic-proteins\nruntime orchestration]

    foundation --> core --> knowledge --> intelligence --> lab --> agentic
    foundation -. stabilizes .-> intelligence
    core -. constrains .-> lab
```

## Why The Split Matters

- ownership is clearer during review
- package contracts stay narrower and easier to defend
- cross-package seams stay visible instead of becoming accidental coupling

## Purpose

This page is the shortest whole-system explanation of the proteomics package
family.

## Stability

Keep it aligned with the current package responsibilities and the reasons the
split exists.
