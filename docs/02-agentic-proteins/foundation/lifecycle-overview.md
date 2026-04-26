---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Lifecycle Overview

Every package run follows a simple lifecycle: inputs enter through interfaces, domain and
application code coordinate the work, and durable artifacts or responses leave
the package.

The value of this page is speed. A reader should be able to skim it and leave
with one coherent story about how work moves through `agentic-proteins` from
entrypoint to result.

Treat the foundation pages for `agentic-proteins` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart RL
    page["Lifecycle Overview<br/>clarifies: own the right work | name the boundary | compare neighbors"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1["trace capture, runtime persistence, and execution-store behavior"]
    own1 --> page
    own2["flow execution authority"]
    own2 --> page
    own3["replay and acceptability semantics"]
    own3 --> page
    limit1["repository tooling and release support"]
    page -.keeps outside.-> limit1
    limit2["agent composition policy"]
    page -.keeps outside.-> limit2
    limit3["ingest and index domain ownership"]
    page -.keeps outside.-> limit3
    anchor1["packages/agentic-proteins"]
    page --> anchor1
    anchor2["packages/agentic-proteins/src/agentic_proteins"]
    page --> anchor2
    anchor3["packages/agentic-proteins/tests"]
    page --> anchor3
    class page page;
    class own1,own2,own3 positive;
    class limit1,limit2,limit3 caution;
    class anchor1,anchor2,anchor3 anchor;
```

## Lifecycle Anchors

- entry surfaces: CLI entrypoint in src/agentic_proteins/interfaces/cli.py, HTTP app in src/agentic_proteins/api/v1, shared API schema in apis/agentic-proteins/v1
- code ownership: src/agentic_proteins/model, src/agentic_proteins/runtime, src/agentic_proteins/application
- durable outputs: execution store records, replay decision artifacts, non-determinism policy evaluations

## Concrete Anchors

- `packages/agentic-proteins` as the package root
- `packages/agentic-proteins/src/agentic_proteins` as the import boundary
- `packages/agentic-proteins/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Lifecycle Overview` to decide whether a change makes `agentic-proteins` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

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

- move to architecture when the question becomes structural rather than boundary-oriented
- move to interfaces when the question becomes contract-facing
- move to quality when the question becomes proof or review sufficiency

## Purpose

This page keeps the package lifecycle readable before a reader dives into implementation detail.

## Stability

Keep it aligned with the current entrypoints and produced outputs.
