---
title: Laboratory Planning and Outcome Contracts
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Laboratory planning and outcome contracts

Lab translates scientific evidence needs into operationally reviewable work and
returns observed outcomes to the evidence system. Its central invariant is that
scientific advice is not an execution instruction.

## Advisory and executable plans

`AdvisoryAssayPlan` records open evidence gaps, assay recommendations, rationale,
and concrete wet-lab actions. It always carries `plan_kind="advisory"` and
`executable=false`.

`ExperimentPlan` groups governed assay requirements into ordered batches by
blocking status and assay family. It retains evidence gaps, blocking review
gates, sample requirements, and per-assay sample kinds. Dependencies constrain
order and cycles are rejected.

`ExecutableAssayPlan` selects one batch and emits instruction IDs, objectives,
sample kinds, blocking posture, and preflight checks. It is ready only when its
declared review gates and sample-kind blockers are clear.

```mermaid
flowchart LR
    need["evidence need"] --> advisory["advisory assay plan"]
    advisory --> design["design and dependency review"]
    design --> batch["experiment batches"]
    batch --> readiness["materials, controls, staff, instrument, review gates"]
    readiness -->|clear| executable["executable assay plan"]
    readiness -->|blocked| refusal["refusal with missing prerequisites"]
```

Execution readiness describes the recorded plan and declared resources. It
does not predict assay success, sample integrity, instrument performance, or
data quality.

## Authorization Envelope

Readiness is evidence for an authorization decision, not the decision itself.
An authorized handoff must bind the plan, selected batch, instruction set,
readiness report, accepted warnings, approving actor, rationale, and approval
time. If any bound identity changes, the handoff returns to review.

```mermaid
flowchart LR
    plan["executable candidate plan"]
    readiness["readiness report"]
    authority{"named authorization"}
    handoff["frozen handoff envelope"]
    refused["refusal or deferred batch"]
    plan --> readiness --> authority
    authority -->|approved| handoff
    authority -->|withheld| refused
```

## Design and readiness

Design contracts make contrasts, biological and technical replication,
randomization, fractionation, multiplex channels, pooled references, spike-in
QC, and carryover risk explicit. Operational readiness combines material and
reagent inventory, staffing, instrument availability, controls, provenance,
evidence sufficiency, and review backlog pressure.

Missing prerequisites are outputs, not defaults. An irresponsible handoff is
represented by `LabExecutionRefusal` with stable reason codes and required
corrections.

## Observed outcomes

An assay observation preserves metric, value, unit, raw replicate values,
summary statistic, dispersion, QC state, normalization, censoring, and
interpretation confidence. An assay outcome distinguishes passed, biological
failure, technical failure, reproducibility failure, and inconclusive states,
with an explicit failure class and uncertainty.

Batch outcomes retain a rerun policy. Evidence promotion readiness checks the
observation and QC posture before converting a lab result into normalized
knowledge evidence.

| Outcome class | Immediate consequence | Evidence consequence |
| --- | --- | --- |
| passed | enter promotion review | may support the requested claim within context and QC limits |
| biological failure | do not repair as technical error | may contradict or narrow the biological claim |
| technical failure | follow the technical rerun policy | does not adjudicate the biological hypothesis |
| reproducibility failure | investigate repeatability and lineage | weakens promotion even if one run looked favorable |
| inconclusive | preserve ambiguity and define missing evidence | cannot be promoted as confirmation or contradiction |

## Reconciliation and feedback

Reconciliation compares planned and observed assay state, records deviations,
and produces operational follow-up plus intelligence feedback. Feedback can
change future priorities, but it must not rewrite the recommendation or plan
that preceded the experiment.

## Contract invariants

- Advisory plans cannot be mistaken for executable instructions.
- Every executable instruction belongs to one batch and names its prerequisites.
- Dependencies, blockers, and missing resources remain explicit.
- Observations preserve replicates, QC, normalization, censoring, and uncertainty.
- Technical, biological, reproducibility, and interpretation failures remain
  distinguishable.
- Evidence promotion is gated and provenance-preserving.
- New outcomes append to decision history rather than revising it silently.

The complete review chain is therefore: recommendation identity, advisory
plan, design, readiness report, authorization, frozen handoff, returned
observations, outcome classification, rerun or promotion verdict, and feedback
record. Missing links must remain visible rather than being reconstructed from
a final narrative.

These contracts put operational authority with laboratory reviewers while
keeping the evidence and decision lineage machine-readable.
