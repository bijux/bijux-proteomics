---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Dependencies and Adjacencies

Dependencies and adjacencies explain what `bijux-proteomics-knowledge` can do by itself and
what it deliberately leans on. They are part of the package story, not just
implementation trivia, because they show where local authority ends.

This page helps a reviewer see both kinds of dependency pressure: library
dependencies that shape the implementation, and neighboring packages that shape
the system boundary.

The foundation pages are the durable package description for `bijux-proteomics-knowledge`. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    dep1["observations and artifacts"]
    dep2["review decisions"]
    dep3["freshness signals"]
    pkg["bijux-proteomics-knowledge<br/>dependency and adjacency view"]
    adj1["bijux-proteomics-intelligence"]
    adj2["bijux-proteomics-lab"]
    adj3["bijux-proteomics-runtime"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    dep1 --> pkg
    dep2 --> pkg
    dep3 --> pkg
    pkg --> adj1
    pkg --> adj2
    pkg --> adj3
    class pkg page;
    class dep1,dep2,dep3 anchor;
    class adj1,adj2,adj3 positive;
```

## Direct Dependency Themes

- agentic-proteins
- bijux-proteomics-foundation
- bijux-proteomics-intelligence
- bijux-proteomics-core
- duckdb
- pydantic

## Adjacent Package Relationships

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` as the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` as the import boundary
- `packages/bijux-proteomics-knowledge/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Dependencies and Adjacencies` to decide whether a change makes `bijux-proteomics-knowledge` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What You Can Resolve Here

- what problem `bijux-proteomics-knowledge` owns on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Review Focus

- compare the stated boundary with the modules, artifacts, and tests that uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Limits

Code, tests, and neighboring package seams remain the proof of this boundary.

## Read Next

- open architecture when the question becomes structural rather than boundary-oriented
- open interfaces when the question becomes contract-facing
- open quality when the question becomes proof or review sufficiency

