---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Domain Language

The language around `bijux-proteomics-knowledge` makes evidence-state and
claim-state discussions precise.

This page keeps the package vocabulary stable enough that docs, code, commit
messages, and review conversations can describe the same idea without drift.

## Visual Summary

```mermaid
flowchart LR
    term1["claim state"]
    term2["contradiction"]
    term3["trust summary"]
    pkg["bijux-proteomics-knowledge<br/>domain language"]
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

- package name: `bijux-proteomics-knowledge`
- Python import root: `bijux_proteomics_knowledge`
- owning package directory: `packages/bijux-proteomics-knowledge`
- key outputs: evidence bundles, claim lineage, conflict resolutions, readiness summaries

## Glossary

- `evidence record`: a single piece of evidence with source, strength, and context.
- `evidence bundle`: a grouped evidence set used for decision-facing evaluation.
- `claim`: a statement linked to evidence with mutable confidence and status.
- `conflict`: incompatible evidence or claim posture requiring policy action.
- `resolution`: policy-selected response that updates claim belief and status.
- `decision readiness`: summary signal for whether evidence posture supports progression.

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` as the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` as the import boundary
- `packages/bijux-proteomics-knowledge/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Domain Language` to decide whether a change makes `bijux-proteomics-knowledge` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What You Can Resolve Here

- what problem `bijux-proteomics-knowledge` is supposed to own on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Review Focus

- compare the stated boundary with the modules, artifacts, and tests that are supposed to uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Limits

This page can explain the intended boundary of `bijux-proteomics-knowledge`, but it cannot prove that boundary by itself. The real proof still lives in the code, tests, and neighboring package seams that either support or contradict the story told here.

## Read Next

- open architecture when the question becomes structural rather than boundary-oriented
- open interfaces when the question becomes contract-facing
- open quality when the question becomes proof or review sufficiency

