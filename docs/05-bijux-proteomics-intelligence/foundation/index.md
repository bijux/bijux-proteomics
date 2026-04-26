---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-04
---

# Foundation

This section explains why `bijux-proteomics-intelligence` exists, what it owns on purpose, and where its boundary stops.

Read this section first when you need the durable package story before code detail. A quick skim should make the role, the boundary, and the neighboring seams legible.

Treat the foundation pages for `bijux-proteomics-intelligence` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    page["Foundation<br/>clarifies: own the right work | name the boundary | compare neighbors"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1["replay and acceptability semantics"]
    own1 --> page
    own2["trace capture, runtime persistence, and execution-store behavior"]
    own2 --> page
    own3["flow execution authority"]
    own3 --> page
    limit1["agent composition policy"]
    page -.keeps outside.-> limit1
    limit2["ingest and index domain ownership"]
    page -.keeps outside.-> limit2
    limit3["repository tooling and release support"]
    page -.keeps outside.-> limit3
    anchor1["packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"]
    page --> anchor1
    anchor2["packages/bijux-proteomics-intelligence/tests"]
    page --> anchor2
    anchor3["packages/bijux-proteomics-intelligence"]
    page --> anchor3
    class page page;
    class own1,own2,own3 positive;
    class limit1,limit2,limit3 caution;
    class anchor1,anchor2,anchor3 anchor;
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

## Read Across the Package

- [Architecture](../architecture/index.md) when the question becomes structural, modular, or execution-oriented
- [Interfaces](../interfaces/index.md) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](../quality/index.md) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `packages/bijux-proteomics-intelligence` as the package root
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence` as the import boundary
- `packages/bijux-proteomics-intelligence/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Foundation` to decide whether a change makes `bijux-proteomics-intelligence` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `bijux-proteomics-intelligence` is supposed to own on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that are supposed to uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page can explain the intended boundary of `bijux-proteomics-intelligence`, but it cannot prove that boundary by itself. The real proof still lives in the code, tests, and neighboring package seams that either support or contradict the story told here.

## Next Checks

- move to architecture when the question becomes structural rather than boundary-oriented
- move to interfaces when the question becomes contract-facing
- move to quality when the question becomes proof or review sufficiency

## Purpose

This page explains how to use the foundation section for `bijux-proteomics-intelligence` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
