---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-22
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

## Preserve custody at every handoff

| Record | Write authority | Becomes immutable when | Later changes appear as |
| --- | --- | --- | --- |
| advisory plan | scientific planning owner | cited by a readiness or decision record | superseding plan with rationale |
| executable plan | assay owner and required approvers | authorized for scheduling or handoff | revision linked to the prior plan; never an in-place protocol rewrite |
| readiness decision | named scientific, operational, and safety authorities | work is released, held, or refused | reevaluation against a new resource and risk snapshot |
| handoff | releasing and receiving custody owners | custody is acknowledged | deviation, amendment, cancellation, or replacement handoff |
| observation | operator and measurement system under the declared protocol | raw evidence and acquisition metadata are sealed | correction or derived record linked to original bytes |
| interpretation and failure classification | accountable reviewer | disposition is issued | superseding review with new evidence or policy identity |
| promotion decision | evidence authority | observation is accepted, qualified, rejected, or held for Knowledge | new promotion review; the observation remains unchanged |

Storage administrators may move or replicate these records without changing
their domain identity. Any transformation that changes content, units,
relationships, or interpretation creates a new artifact with explicit lineage.
