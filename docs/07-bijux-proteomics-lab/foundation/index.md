---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Foundation

This section explains why `bijux-proteomics-lab` exists, what it owns on
purpose, and where its boundary stops.

Read this section first when you need the durable package story before code
detail. A quick skim should make the role, the boundary, and the neighboring
seams legible.

The foundation pages should answer one hard question quickly: why does a
separate lab package exist at all, instead of burying this behavior inside
recommendation logic, runtime orchestration, or knowledge promotion?

## Start Here

```mermaid
flowchart LR
    question["reader question<br/>why is there a dedicated lab package?"]
    pressure["candidate pressure,<br/>review gates, material limits"]
    section["Foundation<br/>role, boundary, non-goals"]
    planning["planning and scheduling<br/>belong here"]
    outcomes["outcome triage and<br/>promotion readiness<br/>belong here"]
    neighbors["recommendation policy,<br/>runtime control, evidence meaning<br/>belong elsewhere"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    question --> pressure
    pressure --> section
    section --> planning
    section --> outcomes
    section --> neighbors
    class question page;
    class section anchor;
    class planning,outcomes positive;
    class neighbors caution;
```

## Pages in This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Ownership Boundary](ownership-boundary.md)
- [Repository Fit](repository-fit.md)
- [Capability Map](capability-map.md)
- [Domain Language](domain-language.md)
- [Lifecycle Overview](lifecycle-overview.md)
- [Dependencies and Adjacencies](dependencies-and-adjacencies.md)
- [Change Principles](change-principles.md)

## What This Section Clarifies

- why planning, scheduling, rerun policy, and promotion readiness belong
  together in one package
- where this package stops and neighboring package ownership begins
- which vocabulary and lifecycle stages reviewers should treat as deliberate
  package concepts rather than incidental implementation detail

## Use This Section When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Do Not Use This Section When

- the boundary question is already settled and you now need module-level
  structure
- the real question is what callers can rely on at the import, schema, or
  artifact level
- the real question is whether the package has enough proof for a change

## Read Across the Package

- [Architecture](../architecture/index.md) when the question becomes how the
  package is organized internally
- [Interfaces](../interfaces/index.md) when the question becomes which imports,
  artifacts, and schemas callers may trust
- [Operations](../operations/index.md) when the question becomes how planning
  and outcome workflows are repeated in practice
- [Quality](../quality/index.md) when the question becomes what evidence proves
  the package contract still holds

## Concrete Anchors

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py` for
  the batch-planning and scheduling boundary
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py` for
  the outcome-triage and promotion-readiness boundary
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py` for
  review-queue and feedback persistence contracts
- `packages/bijux-proteomics-lab/tests/test_experiment_planner.py` and
  `packages/bijux-proteomics-lab/tests/test_outcomes.py` for executable proof
  that the boundary is real

## Reader Takeaway

Use the foundation section to decide whether a question truly belongs to the
lab package before you spend time in lower-level detail. If the work does not
change planning, scheduling, rerun, or promotion readiness, it probably belongs
somewhere else.
