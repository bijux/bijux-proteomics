---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Invariants

Lab invariants prevent advisory work from becoming unauthorized instruction and
prevent returned measurements from becoming stronger evidence than their QC,
reliability, and promotion record permits.

## Laboratory lifecycle invariants

| Invariant | What remains true | Observable violation |
| --- | --- | --- |
| advisory and executable plans differ | executable status requires a concrete batch, instructions, gates, and authority | assay suggestion is sent as operator instruction |
| readiness is conditional | material, instrument, capacity, staffing, controls, provenance, risk, budget, and authority are evaluated for the named context | inventory alone produces `ready` |
| priority never overrides safety | queue rank and schedule cannot bypass controls, dependencies, compatibility, custody, or authorization | urgent work enters a blocked batch |
| handoff freezes approved intent | plan identity, instructions, controls, risk, custody, target mapping, and loss report remain reviewable | export changes the approved assay silently |
| physical execution remains external | package records authorization and receives observations; it does not claim instrument operation | successful serialization is reported as completed experiment |
| observation is immutable in meaning | returned values, missingness, deviations, failures, lineage, and plan link remain distinct from interpretation | reconciliation edits the measurement record |
| completion and acceptance differ | operational return, QC disposition, reliability, and biological interpretation are separate | completed assay is automatically accepted |
| failure and inconclusive are durable | refusal, technical failure, reproducibility failure, biological non-support, and inconclusive remain recoverable | unsuccessful result disappears from the batch summary |
| promotion is explicit and append-only | named policy creates a downstream disposition without rewriting plan or observation | promoted claim replaces adverse QC history |
| feedback preserves history | Knowledge and Intelligence receive new evidence and outcome context | later outcome rewrites the earlier recommendation |

```mermaid
flowchart LR
    P["advisory plan"] --> R["readiness and authority"]
    R --> H["frozen handoff"]
    H --> X["external physical execution"]
    X --> O["immutable observation"]
    O --> Q["QC and reliability"]
    Q --> M["promotion or hold"]
```

## Identity across the loop

Plan, batch, assay, sample, handoff, observation, and promotion identifiers
must allow a reviewer to join records without treating them as the same record.
One assay can yield partial observations, deviations, reruns, and several review
events while the approved intent remains unchanged.

## Failure response

Block the transition whose precondition failed and retain a reason and safe next
action. Do not coerce conditional readiness to ready, infer absent observations,
or promote around failed QC. A refused or inconclusive transition is a valid
laboratory outcome.
