---
title: Foundation
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Foundation

This section explains why `agentic-proteins` still exists, what compatibility
surfaces it preserves on purpose, and where readers should stop treating it as
the center of current runtime work.

Read this section first when you need the durable compatibility story before
code detail. A quick skim makes the bridge role, the retirement boundary,
and the handoff to `bijux-proteomics-runtime` legible.

This section keeps one thing clear: `agentic-proteins` survives to make
migration safer, not to compete with the canonical runtime package for new
design ownership.

## Visual Summary

```mermaid
flowchart LR
    own1["legacy imports"]
    own2["legacy CLI entrypoints"]
    own3["migration-safe forwarding"]
    section["Foundation section<br/>package role and boundary"]
    next1["Architecture"]
    next2["Interfaces"]
    next3["Operations and Quality"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1 --> section
    own2 --> section
    own3 --> section
    section --> next1
    section --> next2
    section --> next3
    class section page;
    class own1,own2,own3 positive;
    class next1,next2,next3 anchor;
```

## Pages in This Section

- [Package Overview](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/change-principles/)

## Open This Section When

- you need to know why a legacy surface still ships at all
- you are checking whether a behavior belongs to compatibility forwarding or to
  canonical runtime ownership
- you need the retirement boundary before reading package detail

## Open Another Section When

- the real question is about current runtime behavior inside
  `bijux-proteomics-runtime`
- you are trying to design new product behavior or broaden the legacy package
- you already know the issue is downstream of the compatibility bridge

## Reader Takeaway

This section is for understanding the compatibility boundary. If the question
stays important after the legacy bridge is removed, it probably belongs in the
runtime handbook rather than here.

## Read Across the Package

- [Architecture](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/) when the question becomes structural, modular, or execution-oriented
- [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `packages/agentic-proteins` as the package root
- `packages/agentic-proteins/src/agentic_proteins` as the import boundary
- `packages/agentic-proteins/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Foundation` to decide whether a change makes `agentic-proteins` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `agentic-proteins` is supposed to own on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that are supposed to uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page can explain the intended boundary of `agentic-proteins`, but it cannot prove that boundary by itself. The real proof still lives in the code, tests, and neighboring package seams that either support or contradict the story told here.

## Next Checks

- open architecture when the question becomes structural rather than boundary-oriented
- open interfaces when the question becomes contract-facing
- open quality when the question becomes proof or review sufficiency

## Purpose

This page explains how to use the foundation section for `agentic-proteins` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
