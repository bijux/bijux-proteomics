---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-intelligence` exists so scoring and recommendation logic stays
auditable and explicit. Its job is to own ranking policies, scenario
evaluators, candidate transitions, and explainability summaries that make
promotion, hold, or redesign decisions reviewable.

If a reader cannot explain this package in one or two sentences after skimming
this page, the package boundary is still too fuzzy and later pages will inherit
that confusion.

Read the foundation pages as the durable package description for
`bijux-proteomics-intelligence`. If the package still feels blurry after this
section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    own1["candidate ranking"]
    own2["scenario evaluation"]
    own3["explainable recommendation policy"]
    pkg["bijux-proteomics-intelligence<br/>durable package role"]
    handoff1["bijux-proteomics-knowledge"]
    handoff2["bijux-proteomics-core"]
    handoff3["bijux-proteomics-lab"]
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

- ranking policy and score decomposition behavior
- scenario and portfolio evaluation logic
- explainability and rejection summary outputs
- candidate transition decision semantics

## What It Does Not Own

- runtime orchestration policy
- evidence collection and lab execution policy
- repository tooling and release support

## Concrete Anchors

- `packages/bijux-proteomics-intelligence` as the package root
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence` as the import boundary
- `packages/bijux-proteomics-intelligence/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Package Overview` to decide whether a change makes `bijux-proteomics-intelligence` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `bijux-proteomics-intelligence` owns on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page shows the intended boundary of `bijux-proteomics-intelligence`, but
it cannot prove that boundary by itself. The real proof still lives in the
code, tests, and neighboring package seams that either support or contradict
the story told here.

## Next Checks

- open architecture when the question becomes structural rather than boundary-oriented
- open interfaces when the question becomes contract-facing
- open quality when the question becomes proof or review sufficiency

## Purpose

This page gives the shortest honest description of what the package is for.

## Stability

Keep it aligned with the real package boundary described by the code and tests.
