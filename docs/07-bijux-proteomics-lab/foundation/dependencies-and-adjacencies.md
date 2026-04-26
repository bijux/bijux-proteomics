---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Dependencies and Adjacencies

Dependencies and adjacencies explain what `bijux-proteomics-lab` can do by itself and
what it deliberately leans on. They are part of the package story, not just
implementation trivia, because they show where local authority ends.

This page should help a reviewer see both kinds of dependency pressure: library
dependencies that shape the implementation, and neighboring packages that shape
the system boundary.

Read the foundation pages as the durable package description for
`bijux-proteomics-lab`. If the package still feels blurry after this section,
the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    dep1["recommended work"]
    dep2["readiness state"]
    dep3["assay dependencies"]
    pkg["bijux-proteomics-lab<br/>dependency and adjacency view"]
    adj1["bijux-proteomics-intelligence"]
    adj2["bijux-proteomics-knowledge"]
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

- `packages/bijux-proteomics-lab` as the package root
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab` as the import boundary
- `packages/bijux-proteomics-lab/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Dependencies and Adjacencies` to decide whether a change makes `bijux-proteomics-lab` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `bijux-proteomics-lab` owns on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page shows the intended boundary of `bijux-proteomics-lab`, but it cannot
prove that boundary by itself. The real proof still lives in the code, tests,
and neighboring package seams that either support or contradict the story told
here.

## Next Checks

- open architecture when the question becomes structural rather than boundary-oriented
- open interfaces when the question becomes contract-facing
- open quality when the question becomes proof or review sufficiency

## Purpose

This page shows which surrounding tools and packages `bijux-proteomics-lab`
depends on to do its job.

## Stability

Keep it aligned with `pyproject.toml` and the actual package seams.
