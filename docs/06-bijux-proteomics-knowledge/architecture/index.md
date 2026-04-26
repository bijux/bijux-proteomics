---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Architecture

Use this section when the question is structural: which modules own evidence
bundles, claim state, conflict resolution, review packets, schema
compatibility, and graph relationships, and how those pieces fit together
without turning the knowledge layer into a vague storage bucket.

`bijux-proteomics-knowledge` is feature-oriented rather than framework-layered.
Evidence enters through adapters, becomes structured records and bundles, moves
through claim and resolution logic, and ends up in review and readiness
surfaces that other packages can inspect.

## Visual Summary

```mermaid
flowchart LR
    adapters["adapters and ingestion normalization"]
    evidence["evidence, repositories, and bundle state"]
    claims["claims, graph, and lineage"]
    resolution["resolution and contradiction handling"]
    review["review packets, confidence, and readiness"]
    reader["reader question<br/>where does this knowledge behavior live?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class adapters,page reader;
    class evidence,claims,resolution positive;
    class review anchor;
    adapters --> evidence --> claims --> resolution --> review
    evidence --> reader
    claims --> reader
    resolution --> reader
```

## Start Here

- use [Module Map](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/module-map/) for the shortest route from filenames to
  owned behavior
- use [Execution Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/execution-model/) when you need the flow from
  ingested evidence to reviewed knowledge state
- use [State and Persistence](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/state-and-persistence/) when the question is
  which records, repositories, or summaries become durable

## Pages In Architecture

- [Module Map](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/architecture-risks/)

## Use This Section When

- you need to know which module family owns a behavior before editing it
- a review is about decomposition, dependency direction, or execution flow
- you need to explain how evidence, claims, resolution, and review structure
  relate

## Move On When

- the main question is why the package owns the behavior at all
- you are deciding whether a schema, import, or artifact is a public contract
- the issue is procedural or proof-oriented rather than structural

## Read Across The Package

- use [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/) for package purpose and ownership
- use [Interfaces](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/) for import, schema, serialization,
  and artifact contracts
- use [Operations](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/) for workflow, diagnostics, and
  release procedures
- use [Quality](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/quality/) for invariants, tests, and structure-risk
  pressure

## Concrete Anchors

- `src/bijux_proteomics_knowledge/adapters.py` for input normalization and
  ingestion helpers
- `src/bijux_proteomics_knowledge/evidence.py`, `repositories.py`, and
  `serialization.py` for durable record and bundle state
- `src/bijux_proteomics_knowledge/claims.py`, `graph.py`, and `resolution.py`
  for claim lifecycle, contradiction handling, and dependency relationships
- `src/bijux_proteomics_knowledge/review.py` and `confidence/` for review
  packets, confidence, and readiness summaries

## Reader Takeaway

`Architecture` should make the knowledge package legible as a chain of named
responsibilities. If evidence storage, claim semantics, contradiction handling,
and review output start blending together, the package becomes harder to trust
as an auditable state layer.

## What You Get

This page gives you the module, dependency, execution, and durable-state route
through `bijux-proteomics-knowledge` before you inspect a specific structural
topic.
