---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Error Model

Lab represents planning blockers, operational failures, scientific outcomes, and promotion conflicts separately because each demands a different response.

| Condition | Representation | Response |
| --- | --- | --- |
| Invalid design | Experiment design or plan validation issue | Correct cohorts, controls, assays, dependencies, or metadata |
| Dependency cycle | Dependency cycle or integrity report | Repair the plan before scheduling |
| Resource blocker | Readiness report naming instruments, materials, staffing, cost, or backlog | Defer or re-plan; do not mark execution ready |
| Missing control or provenance | Readiness blocker or artifact contract issue | Restore the required control or lineage before handoff |
| Transition refusal | Approved, exploratory, or refused targeted-transition disposition | Restrict or reject the transition with reasons |
| Technical failure | `FAILED_TECHNICAL` and technical failure class | Diagnose execution and apply the declared rerun policy |
| Reproducibility failure | `FAILED_REPRODUCIBILITY` | Review dispersion, batches, protocol, and repeats |
| Biological failure | `FAILED_BIOLOGICAL` | Retain as interpretable adverse evidence; do not relabel as technical |
| Inconclusive outcome | `INCONCLUSIVE` with uncertainty and caveats | Hold promotion or request resolving work |
| Promotion conflict | Blocked promotion state or audit issue | Preserve the observation and resolve the promotion gate |

```mermaid
flowchart TD
    P[Planned work] --> V{Plan and readiness valid?}
    V -->|no| B[Blocked with named findings]
    V -->|yes| O[Observe]
    O --> Q{QC and interpretation}
    Q -->|technical| T[Rerun or repair]
    Q -->|biological| E[Adverse evidence]
    Q -->|inconclusive| H[Hold and resolve]
    Q -->|supported| R[Promotion review]
```

A failed acceptance rule does not identify the failure class by itself. QC, replicate behavior, controls, material state, censoring, and protocol context determine whether the correct response is rerun, redesign, adverse-evidence promotion, or refusal to interpret.
