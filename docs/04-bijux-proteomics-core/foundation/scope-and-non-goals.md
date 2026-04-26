---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Scope and Non-Goals

This page names the line that keeps `bijux-proteomics-core` useful instead of bloated.
The point of a package boundary is not to make work harder. It is to keep
neighboring packages from silently accumulating overlapping authority.

The non-goals matter as much as the goals. A package becomes easier to trust
when readers can see what it refuses to absorb just because the code happens to
be nearby.

Treat the foundation pages for `bijux-proteomics-core` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    pkg["Scope boundary<br/>for bijux-proteomics-core"]
    own1["program contracts"]
    own2["lifecycle and readiness rules"]
    own3["deterministic validation"]
    out1["evidence policy"]
    out2["lab scheduling"]
    out3["repository automation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1 --> pkg
    own2 --> pkg
    own3 --> pkg
    pkg -.stays outside.-> out1
    pkg -.stays outside.-> out2
    pkg -.stays outside.-> out3
    class pkg page;
    class own1,own2,own3 positive;
    class out1,out2,out3 caution;
```

## In Scope

- flow execution authority
- replay and acceptability semantics
- trace capture, runtime persistence, and execution-store behavior
- package-local CLI and API boundaries

## Out of Scope

- agent composition policy
- ingest and index domain ownership
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

Use `Scope and Non-Goals` to decide whether a change makes `bijux-proteomics-core` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What This Page Answers

- what problem `bijux-proteomics-core` is supposed to own on purpose
- where the package boundary stops, even when nearby code looks tempting
- which neighboring package seams deserve comparison before the boundary is changed

## Reviewer Lens

- compare the stated boundary with the modules, artifacts, and tests that are supposed to uphold it
- check that out-of-scope behavior is not quietly re-entering through convenience paths
- confirm that the package story still matches the real repository layout and neighboring package docs

## Honesty Boundary

This page can explain the intended boundary of `bijux-proteomics-core`, but it cannot prove that boundary by itself. The real proof still lives in the code, tests, and neighboring package seams that either support or contradict the story told here.

## Next Checks

- move to architecture when the question becomes structural rather than boundary-oriented
- move to interfaces when the question becomes contract-facing
- move to quality when the question becomes proof or review sufficiency

## Purpose

This page keeps future work from leaking into the wrong package.

## Stability

Update it only when ownership truly moves into or out of `bijux-proteomics-core`.
