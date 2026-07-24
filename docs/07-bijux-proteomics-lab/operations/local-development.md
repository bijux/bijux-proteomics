---
title: Local Development
audience: developer
type: how-to
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Local development

Lab owns the boundary between advisory follow-up and reviewed physical work:
assay planning, experimental design, batching, readiness, handoffs, outcomes,
and reconciliation. Local changes must preserve who authorized execution, what
was expected, what was actually observed, and why a run was refused or altered.

## Run package-scoped gates

Use root package dispatch:

```bash
make lint PACKAGE=bijux-proteomics-lab
make test PACKAGE=bijux-proteomics-lab
make quality PACKAGE=bijux-proteomics-lab
make api PACKAGE=bijux-proteomics-lab
```

Run `make build PACKAGE=bijux-proteomics-lab` when root exports, handoff
artifacts, compatibility forwarding, package data, or metadata changes. Store
generated examples and reports under `artifacts/`.

## Trace authority and observation

```mermaid
flowchart LR
    advice["advisory follow-up"]
    review["human review and readiness"]
    execution["authorized instructions"]
    observed["observed outcome"]
    reconcile["deviation and follow-up"]
    advice --> review --> execution --> observed --> reconcile
```

Start in the owning domain: `planning/` for assay intent and batches, `design/`
for protocols and experimental structure, `readiness/` for execution gates,
`handoffs/` for operator payloads, `outcomes/` for observations, and
`reconciliation/` for comparison and follow-up. Serialization preserves these
contracts; it must not promote advice into executable instructions.

## Prove operational boundaries

| Change | Required evidence |
| --- | --- |
| advisory plan | remains non-executable and carries rationale and blockers |
| readiness gate | ready, not-ready, missing-resource, and review-backlog cases |
| executable handoff | authority, protocol, materials, controls, and preflight remain explicit |
| scheduling or batching | dependency, capacity, delay, cycle, and infeasible cases |
| outcome model | raw values, units, QC, censoring, deviations, and failures survive round trip |
| reconciliation | expected and observed states remain separate and prior records stay immutable |

Use computational fixtures for contract logic. Do not describe them as evidence
that an instrument, protocol, or assay performs successfully in the physical
world. Operational performance claims require measured laboratory evidence.

## Preserve refusal and ownership

Refusal is correct when materials, controls, evidence, staffing, instrument
capacity, or review authority are insufficient. Do not replace it with a
default plan that appears executable. Lab consumes scientific and advisory
inputs but does not redefine Core calculations, Knowledge evidence, or
Intelligence recommendations.

The change is ready when advisory and executable states cannot be confused,
authority is recoverable, idempotent handoff behavior is tested, observations
remain distinct from expectations, and reconciliation records every meaningful
deviation without rewriting history.
