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
detail. A quick skim makes the role, the boundary, and the neighboring
seams legible.

The foundation pages answer one hard question quickly: why does a
separate lab package exist at all, instead of burying this behavior inside
recommendation logic, runtime orchestration, or knowledge promotion?

## Start Here

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/change-principles/)

## What This Section Clarifies

- why planning, scheduling, rerun policy, and promotion readiness belong
  together in one package
- where this package stops and neighboring package ownership begins
- which vocabulary and lifecycle stages reviewers should treat as deliberate
  package concepts rather than incidental implementation detail

## Open This Section When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Open Another Section When

- the boundary question is already settled and you now need module-level
  structure
- the real question is what callers can rely on at the import, schema, or
  artifact level
- the real question is whether the package has enough proof for a change

## Read Across the Package

- open [Architecture](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/) when the question becomes how the
  package is organized internally
- open [Interfaces](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/) when the question becomes which imports,
  artifacts, and schemas callers may trust
- open [Operations](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/) when the question becomes how planning
  and outcome workflows are repeated in practice
- open [Quality](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/quality/) when the question becomes what evidence proves
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

## Bottom Line

Open the foundation section to decide whether a question truly belongs to the
lab package before you spend time in lower-level detail. If the work does not
change planning, scheduling, rerun, or promotion readiness, it probably belongs
somewhere else.
