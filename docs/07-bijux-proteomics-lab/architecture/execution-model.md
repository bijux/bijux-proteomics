---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Execution Model

The lab loop advances through explicit contracts. Advisory planning answers what evidence would be useful. Executable planning answers whether a concrete batch can be handed to operators. Outcome handling answers what happened and whether the result is fit to return to knowledge.

```mermaid
stateDiagram-v2
    [*] --> Advisory
    Advisory --> ExecutableReview: assay intent and dependencies resolved
    ExecutableReview --> Blocked: readiness finding
    Blocked --> ExecutableReview: finding resolved
    ExecutableReview --> Ready: operational gates pass
    Ready --> InReview: execution returns observations
    InReview --> Rerun: technical or reproducibility failure
    InReview --> PromotionReview: interpretable outcome
    Rerun --> ExecutableReview
    PromotionReview --> Promoted: provenance and evidence checks pass
    PromotionReview --> Blocked: evidence remains insufficient
```

## From evidence gap to batch

Planning maps open evidence needs to assays, prerequisites, sample kinds, blocking gates, and ordered batches. Advisory plans remain `executable = false`. Building an executable plan adds concrete instruction and batch identities plus preflight checks, but `ready_for_execution` still reflects blockers rather than bypassing them.

Readiness evaluates live constraints: instrument and material availability, capacity, staffing, cost, backlog pressure, required controls, input lineage, and evidence strength. The report names deferred batches and blocking resources. Warning and blocking provenance findings remain distinguishable.

## Handoff and observation

```mermaid
sequenceDiagram
    participant Science as Evidence owner
    participant Plan as Lab planning
    participant Gate as Readiness review
    participant Ops as Laboratory operation
    participant Outcome as Outcome review
    Science->>Plan: evidence gaps and program contract
    Plan->>Gate: executable candidate plan
    Gate-->>Ops: approved handoff artifacts
    Ops-->>Outcome: observations, QC, replicates, lineage
    Outcome-->>Science: promoted evidence or explicit hold
```

Handoff artifacts freeze the approved intent and explain risks, controls, and expected outputs. Physical execution occurs outside this Python package. Returned observations are judged against assay definitions and acceptance rules, then classified as passed, biological failure, technical failure, reproducibility failure, or inconclusive.

## Reconciliation and audit

Rerun policy follows the failure class rather than a generic failed flag. Review-queue and assay-lifecycle transitions are validated and timestamped; broken histories are audit findings. Promotion is separately recorded as pending, ready, blocked, promoted, or superseded. This makes the full loop reviewable without pretending that planning, execution, interpretation, and evidence acceptance are the same event.
