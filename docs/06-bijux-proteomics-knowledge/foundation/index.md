---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Foundation

Use this section when you need the durable answer to a simple question: why
does `bijux-proteomics-knowledge` exist as its own package between shared
payload contracts below and decision or lab policy above?

This package is where proteomics evidence stops being merely available and
starts becoming auditable knowledge. It owns evidence records, claim state,
conflict resolution, trust summaries, and review packets that later packages
consume when they decide what to recommend or promote.

## Visual Summary

```mermaid
flowchart LR
    inputs["literature, assay, and manual evidence inputs"]
    records["evidence bundles and evidence records"]
    claims["claim state, lineage, and contradiction handling"]
    trust["trust, freshness, and readiness summaries"]
    handoff["intelligence and lab consume inspected knowledge state"]
    reader["reader question<br/>what belongs in the knowledge layer?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class inputs,page reader;
    class records,claims,trust positive;
    class handoff anchor;
    inputs --> records --> claims --> trust --> handoff
    records --> reader
    claims --> reader
    trust --> reader
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest statement of
  the package role
- open [Ownership Boundary](ownership-boundary.md) when the question is whether
  logic belongs in foundation, intelligence, lab, or runtime
- open [Lifecycle Overview](lifecycle-overview.md) when you need the path from
  evidence ingestion to auditable readiness output

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Ownership Boundary](ownership-boundary.md)
- [Repository Fit](repository-fit.md)
- [Capability Map](capability-map.md)
- [Domain Language](domain-language.md)
- [Lifecycle Overview](lifecycle-overview.md)
- [Dependencies and Adjacencies](dependencies-and-adjacencies.md)
- [Change Principles](change-principles.md)

## Use This Section When

- you need the package role before looking at modules, schemas, or tests
- you are deciding whether behavior is really about evidence state rather than
  decision policy or lab execution
- a reader needs one page that explains why the knowledge layer exists without
  reading the whole handbook

## Do Not Use This Section When

- the main question is where a module or import surface lives
- you are deciding whether a schema, artifact, or import is a supported
  contract
- the issue is procedural or proof-oriented rather than boundary-oriented

## Read Across The Package

- open [Architecture](../architecture/index.md) for module groups, execution
  flow, and persistence seams
- open [Interfaces](../interfaces/index.md) for schemas, serialization,
  artifacts, and import contracts
- open [Operations](../operations/index.md) for package workflows, diagnostics,
  and release procedures
- open [Quality](../quality/index.md) for proof surfaces, invariants, and
  limits

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` as the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` as the import boundary
- `packages/bijux-proteomics-knowledge/tests` as the package proof surface

## Reader Takeaway

`Foundation` should leave no doubt about the package boundary: foundation keeps
shared payload meaning stable, knowledge records and evaluates evidence state,
intelligence chooses among options, and lab turns chosen work into outcomes.

## Purpose

This page introduces the knowledge foundation handbook and routes readers to
the pages that explain purpose, scope, vocabulary, lifecycle, and boundaries.
