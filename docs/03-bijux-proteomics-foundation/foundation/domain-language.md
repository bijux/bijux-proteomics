---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Domain Language

The language around `bijux-proteomics-foundation` should reinforce the real package
boundary. Good names shorten review. Weak names force people to keep asking
whether they are looking at local behavior or at something owned elsewhere.

This page keeps the package vocabulary stable enough that docs, code, commit
messages, and review conversations can describe the same idea without drift.

Treat the foundation pages for `bijux-proteomics-foundation` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    term1["payload shape"]
    term2["canonical serialization"]
    term3["compatibility helper"]
    pkg["bijux-proteomics-foundation<br/>domain language"]
    reader1["reviewers"]
    reader2["developers"]
    reader3["maintainers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    term1 --> pkg
    term2 --> pkg
    term3 --> pkg
    pkg --> reader1
    pkg --> reader2
    pkg --> reader3
    class pkg page;
    class term1,term2,term3 anchor;
    class reader1,reader2,reader3 positive;
```

## Package Vocabulary Anchors

- package name: `bijux-proteomics-foundation`
- Python import root: `bijux_proteomics_foundation`
- owning package directory: `packages/bijux-proteomics-foundation`
- key outputs: execution store records, replay decision artifacts, non-determinism policy evaluations

## Concrete Anchors

- `packages/bijux-proteomics-foundation` as the package root
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation` as the import boundary
- `packages/bijux-proteomics-foundation/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Domain Language` to decide whether a change makes `bijux-proteomics-foundation` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `bijux-proteomics-foundation` is supposed to own on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that are supposed to uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page can explain the intended boundary of `bijux-proteomics-foundation`, but it cannot prove that boundary by itself. The real proof still lives in the code, tests, and neighboring package seams that either support or contradict the story told here.

## Next Checks

- move to architecture when the question becomes structural rather than boundary-oriented
- move to interfaces when the question becomes contract-facing
- move to quality when the question becomes proof or review sufficiency

## Purpose

This page records the naming anchors that should stay stable in docs, code, and review discussions.

## Stability

Keep it aligned with the package's real import names, directories, and artifact nouns.
