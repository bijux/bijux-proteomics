---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# State and Persistence

Lab state records the changing contract between scientific intent and physical work. Plans, readiness, handoffs, observations, reviews, and promotion decisions remain distinct durable records linked by stable identifiers.

```mermaid
flowchart LR
    A[Advisory plan] --> X[Executable plan]
    X --> R[Readiness report]
    R --> H[Handoff artifacts]
    H --> O[Observation records]
    O --> F[Failure triage and feedback]
    O --> P[Promotion decision]
    P --> N[Normalized evidence input]
    A --> L[Lifecycle audit]
    X --> L
    R --> L
    P --> L
```

## Durable lab state

- plan identity, kind, evidence gaps, assay intent, dependencies, batches, priority, samples, gates, and preflight checks;
- readiness inputs and findings for capacity, instruments, materials, staffing, budget, controls, provenance, evidence, and queue pressure;
- handoff artifacts, compatibility reports, contract issues, explanations, risks, exports, and approved transition lists;
- observations with metric, unit, replicate values, dispersion, normalization, QC, detection limits, censoring, batch concerns, and interpretation confidence;
- outcomes with result state, failure class, uncertainty, acceptance rule, and rerun policy;
- review-queue, assay-lifecycle, and promotion transitions with actor, reason, time, and audit issues;
- feedback, reconciliation, anomaly, latency, lineage-coverage, and outcome-dossier reports.

## Ownership and immutability

Runtime may persist and transport these documents, but lab owns their operational meaning. Knowledge owns the normalized evidence after successful promotion. A later plan, rerun, or interpretation supersedes earlier state through linked records; it does not overwrite the approved handoff or original observation.

This separation allows a reviewer to reconstruct what was proposed, what was authorized, what was performed, what was observed, and what was finally accepted as evidence.
