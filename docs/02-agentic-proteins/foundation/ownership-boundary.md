---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Ownership Boundary

Ownership in `agentic-proteins` should be visible in checked-in structure, not
only in prose. The source tree shows where the package expects work to live, and
the tests show whether that expectation is protected when the code changes.

Use this page when a change proposal feels plausible in more than one package
and someone needs a concrete reason to keep the work here or move it elsewhere.

Treat the foundation pages for `agentic-proteins` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart TB
    page["Ownership Boundary<br/>clarifies: own the right work | name the boundary | compare neighbors"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    own1["legacy import forwarding"]
    own1 --> page
    own2["compatibility CLI and API entrypoints"]
    own2 --> page
    own3["migration-safe import surfaces"]
    own3 --> page
    limit1["canonical runtime execution authority"]
    page -.keeps outside.-> limit1
    limit2["repository tooling and release support"]
    page -.keeps outside.-> limit2
    limit3["agent composition policy"]
    page -.keeps outside.-> limit3
    anchor1["packages/agentic-proteins/src/agentic_proteins"]
    page --> anchor1
    anchor2["packages/agentic-proteins/tests"]
    page --> anchor2
    anchor3["packages/agentic-proteins"]
    page --> anchor3
    class page page;
    class own1,own2,own3 positive;
    class limit1,limit2,limit3 caution;
    class anchor1,anchor2,anchor3 anchor;
```

## Owned Code Areas

- `src/agentic_proteins/interfaces` for compatibility CLI forwarding
- `src/agentic_proteins/api` for compatibility API forwarding
- `src/agentic_proteins/**` forwarding modules that preserve legacy import
  paths while delegating behavior to canonical packages

## Adjacent Systems

- defers runtime authority to `bijux-proteomics-runtime`
- defers domain authority to foundation/core/knowledge/intelligence/lab

## Concrete Anchors

- `packages/agentic-proteins` as the package root
- `packages/agentic-proteins/src/agentic_proteins` as the import boundary
- `packages/agentic-proteins/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Ownership Boundary` to decide whether a change makes `agentic-proteins` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

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

This page ties package ownership to concrete directories instead of abstract slogans.

## Stability

Keep it aligned with the current module layout.
