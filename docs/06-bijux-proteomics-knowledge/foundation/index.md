---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Foundation

Open this section when you need the durable answer to a simple question: why
does `bijux-proteomics-knowledge` exist as its own package between shared
payload contracts below and decision or lab policy above?

This package is where proteomics evidence stops being merely available and
starts becoming auditable knowledge. It owns evidence records, claim state,
conflict resolution, trust summaries, and review packets that later packages
consume when they decide what to recommend or promote.

## Start Here

- open [Package Overview](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/package-overview/) for the shortest statement of
  the package role
- open [Ownership Boundary](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/ownership-boundary/) when the question is whether
  logic belongs in foundation, intelligence, lab, or runtime
- open [Lifecycle Overview](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/lifecycle-overview/) when you need the path from
  evidence ingestion to auditable readiness output

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/change-principles/)

## Open This Section When

- you need the package role before looking at modules, schemas, or tests
- you are deciding whether behavior is really about evidence state rather than
  decision policy or lab execution
- a reader needs one page that explains why the knowledge layer exists without
  reading the whole handbook

## Open Another Section When

- the main question is where a module or import surface lives
- you are deciding whether a schema, artifact, or import is a supported
  contract
- the issue is procedural or proof-oriented rather than boundary-oriented

## Read Across The Package

- open [Architecture](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/) for module groups, execution
  flow, and persistence seams
- open [Interfaces](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/) for schemas, serialization,
  artifacts, and import contracts
- open [Operations](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/) for package workflows, diagnostics,
  and release procedures
- open [Quality](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/quality/) for proof surfaces, invariants, and
  limits

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` as the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` as the import boundary
- `packages/bijux-proteomics-knowledge/tests` as the package proof surface

## Bottom Line

`Foundation` should leave no doubt about the package boundary: foundation keeps
shared payload meaning stable, knowledge records and evaluates evidence state,
intelligence chooses among options, and lab turns chosen work into outcomes.

