---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-04
---

# Change Principles

Changes in `bijux-proteomics-core` should leave the package easier to explain, not
harder. A good change makes ownership clearer, contract language more honest,
and the proof story easier to follow.

These principles are not slogans. They are the filter for deciding whether a
local improvement is worth the long-term cost it creates for the rest of the
system.

Treat the foundation pages for `bijux-proteomics-core` as the package's durable self-description. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart RL
    page["Change Principles<br/>clarifies: own the right work | name the boundary | compare neighbors"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    own1["trace capture, runtime persistence, and execution-store behavior"]
    own1 --> page
    own2["flow execution authority"]
    own2 --> page
    own3["replay and acceptability semantics"]
    own3 --> page
    limit1["ingest and index domain ownership"]
    page -.keeps outside.-> limit1
    limit2["repository tooling and release support"]
    page -.keeps outside.-> limit2
    limit3["agent composition policy"]
    page -.keeps outside.-> limit3
    anchor1["packages/bijux-proteomics-core/src/bijux_proteomics"]
    page --> anchor1
    anchor2["packages/bijux-proteomics-core/tests"]
    page --> anchor2
    anchor3["packages/bijux-proteomics-core"]
    page --> anchor3
    class page page;
    class own1,own2,own3 positive;
    class limit1,limit2,limit3 caution;
    class anchor1,anchor2,anchor3 anchor;
```

## Principles

- prefer moving behavior toward the owning package instead of letting boundary overlap grow
- update docs and tests in the same change series that changes package behavior
- keep names stable and descriptive enough to survive years of maintenance

## Concrete Anchors

- `packages/bijux-proteomics-core` as the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics` as the import boundary
- `packages/bijux-proteomics-core/tests` as the package proof surface

## Use This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Change Principles` to decide whether a change makes `bijux-proteomics-core` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

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

This page records the package-specific contribution posture.

## Stability

Update these principles only when the package operating model truly changes.
