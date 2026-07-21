---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Architecture Risks

Lab risk begins when a recommendation, plan, readiness assessment, completed run, or promoted outcome is treated as if it proves all the others.

| Risk | Consequence | Control |
| --- | --- | --- |
| Advisory-to-execution collapse | Scientifically useful work is scheduled without operational review | Keep advisory plans non-executable and require explicit executable plans |
| Stale readiness | Capacity, inventory, staffing, controls, or backlog changes after approval | Bind readiness to a dated snapshot and re-evaluate before handoff |
| Dependency failure | An assay starts before prerequisite evidence or work exists | Validate dependency integrity and cycles |
| Missing controls | Results cannot distinguish signal from technical or procedural artifact | Make control absence blocking for affected batches |
| Provenance gap | Observations cannot be traced to approved intent, inputs, or operators | Gate execution and promotion on lineage completeness |
| Failure-class collapse | Technical failure is interpreted as biological failure, or vice versa | Preserve normalized result state and failure class |
| Censoring blindness | Below-detection measurements are treated as ordinary quantitative values | Retain detection limit, direction, and censoring flag |
| Promotion leakage | Raw or weak observations enter knowledge as accepted evidence | Require a separate promotion review and normalized evidence contract |
| Queue bias | Candidate score crowds out cost, capacity, evidence gaps, and assay burden | Preserve prioritization factors and queue rationale |

```mermaid
flowchart LR
    A[Advisory] --> E[Executable plan]
    E --> R[Readiness snapshot]
    R --> H[Handoff]
    H --> O[Observation]
    O --> T[Failure triage and interpretation]
    T --> P[Promotion review]
    P --> K[Knowledge evidence]
```

The gates deliberately repeat validation at changing boundaries. A scientifically justified assay can remain operationally irresponsible, and a well-executed assay can remain evidentially inconclusive.
