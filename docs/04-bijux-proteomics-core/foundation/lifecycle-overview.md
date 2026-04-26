---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Lifecycle Overview

Every package run follows a simple lifecycle: inputs enter through interfaces, domain and
application code coordinate the work, and durable artifacts or responses leave
the package.

This page is built for speed. It gives one coherent story about how work moves through `bijux-proteomics-core` from entrypoint to result.

The foundation pages are the durable package description for `bijux-proteomics-core`. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    in1["shared payload contracts"]
    in2["program changes"]
    in3["validation requirements"]
    pkg["bijux-proteomics-core<br/>lifecycle role"]
    out1["validated programs"]
    out2["lifecycle transitions"]
    out3["downstream constraints"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    in1 --> pkg
    in2 --> pkg
    in3 --> pkg
    pkg --> out1
    pkg --> out2
    pkg --> out3
    class pkg page;
    class in1,in2,in3 anchor;
    class out1,out2,out3 positive;
```

## Lifecycle Anchors

- entry surfaces: CLI entrypoint in src/bijux_proteomics/interfaces/cli.py, HTTP app in src/bijux_proteomics/programs.py, program schemas in src/bijux_proteomics/programs.py
- code ownership: src/bijux_proteomics/model, src/bijux_proteomics/runtime, src/bijux_proteomics/application
- durable outputs: execution store records, replay decision artifacts, non-determinism policy evaluations

## Concrete Anchors

- `packages/bijux-proteomics-core` as the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics` as the import boundary
- `packages/bijux-proteomics-core/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Lifecycle Overview` to decide whether a change makes `bijux-proteomics-core` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What You Can Resolve Here

- what problem `bijux-proteomics-core` owns on purpose
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

