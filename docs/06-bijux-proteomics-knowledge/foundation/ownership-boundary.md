---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Ownership in `bijux-proteomics-knowledge` should be visible in checked-in structure, not
only in prose. The source tree shows where the package expects work to live, and
the tests show whether that expectation is protected when the code changes.

Use this page when a change proposal feels plausible in more than one package
and someone needs a concrete reason to keep the work here or move it elsewhere.

The foundation pages are the durable package description for `bijux-proteomics-knowledge`. If the package still feels blurry after this section, the boundary story is not clear enough yet.

## Visual Summary

```mermaid
flowchart LR
    own1["evidence records"]
    own2["claim transitions"]
    own3["trust and contradiction handling"]
    boundary["Ownership boundary<br/>for bijux-proteomics-knowledge"]
    handoff1["bijux-proteomics-intelligence"]
    handoff2["bijux-proteomics-lab"]
    handoff3["bijux-proteomics-runtime"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    own1 --> boundary
    own2 --> boundary
    own3 --> boundary
    boundary --> handoff1
    boundary --> handoff2
    boundary --> handoff3
    class boundary page;
    class own1,own2,own3 positive;
    class handoff1,handoff2,handoff3 caution;
```

## Owned Code Areas

- `src/bijux_proteomics_knowledge/model` for durable runtime models
- `src/bijux_proteomics_knowledge/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_knowledge/application` for orchestration and replay coordination
- `src/bijux_proteomics_knowledge/verification` for runtime-level validation support
- `src/bijux_proteomics_knowledge/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_knowledge/api` for HTTP application surfaces

## Adjacent Systems

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` as the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` as the import boundary
- `packages/bijux-proteomics-knowledge/tests` as the package proof surface

## Open This Page When

- you need the package idea before the implementation detail
- you are deciding whether work belongs here or in a neighboring package
- you want the shortest honest explanation of what this package is for

## Decision Rule

Use `Ownership Boundary` to decide whether a change makes `bijux-proteomics-knowledge` easier or harder to defend as one distinct role in the overall system. If the work makes the package broader without making its role clearer, stop and re-check the boundary before treating the change as a local improvement.

## What You Can Resolve Here

- what problem `bijux-proteomics-knowledge` owns on purpose
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

