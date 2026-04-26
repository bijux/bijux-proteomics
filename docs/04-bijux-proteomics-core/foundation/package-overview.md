---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-core` exists so target programs and decision gates are
described with explicit, stable contracts. Its job is to own domain models for
program intent, target and assay definitions, lifecycle transitions, and
validation rules consumed by intelligence, knowledge, and lab layers.

If a reader cannot explain this package in one or two sentences after skimming
this page, the package boundary is still too fuzzy and later pages will inherit
that confusion.

The foundation pages are the durable package description for `bijux-proteomics-core`. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    own1["program contracts"]
    own2["lifecycle and readiness rules"]
    own3["deterministic validation"]
    pkg["bijux-proteomics-core<br/>durable package role"]
    handoff1["bijux-proteomics-foundation"]
    handoff2["bijux-proteomics-intelligence"]
    handoff3["bijux-proteomics-runtime"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1 --> pkg
    own2 --> pkg
    own3 --> pkg
    pkg --> handoff1
    pkg --> handoff2
    pkg --> handoff3
    class pkg page;
    class own1,own2,own3 positive;
    class handoff1,handoff2,handoff3 anchor;
```

## What It Owns

- program definitions and lifecycle contracts
- domain validation and identifier consistency rules
- constraints and review-gate model semantics
- runtime adapter boundary for integrating program models

## What It Does Not Own

- runtime orchestration policy
- evidence and assay outcome policy
- repository tooling and release support

## Concrete Anchors

- `packages/bijux-proteomics-core` as the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics` as the import boundary
- `packages/bijux-proteomics-core/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Package Overview` to decide whether a change makes `bijux-proteomics-core` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

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

