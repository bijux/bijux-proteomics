---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams are the points where `bijux-proteomics-intelligence` meets configuration, APIs,
operators, or neighboring packages.

This page exists so integration changes do not feel mysterious. A reviewer should
be able to say which seams are intentional, which ones carry compatibility risk,
and where the package expects outside systems to meet it.

Treat the architecture pages for `bijux-proteomics-intelligence` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart LR
    seam1["knowledge evidence seam"]
    seam2["core contract seam"]
    seam3["lab planning seam"]
    page["bijux-proteomics-intelligence<br/>integration seams"]
    review1["caller expectations"]
    review2["contract alignment"]
    review3["drift checks"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    seam1 --> page
    seam2 --> page
    seam3 --> page
    page --> review1
    page --> review2
    page --> review3
    class page page;
    class seam1,seam2,seam3 anchor;
    class review1,review2,review3 action;
```

## Integration Surfaces

- CLI entrypoint in src/bijux_proteomics_intelligence/briefs.py
- HTTP app in src/bijux_proteomics_intelligence/evaluators.py
- ranking contracts in src/bijux_proteomics_intelligence/policies.py

## Adjacent Systems

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `src/bijux_proteomics_intelligence/model` for durable runtime models
- `src/bijux_proteomics_intelligence/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_intelligence/application` for orchestration and replay coordination

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Integration Seams` to decide whether a structural change makes `bijux-proteomics-intelligence` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-intelligence` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-intelligence`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- move to interfaces when the review reaches a public or operator-facing seam
- move to operations when the concern becomes repeatable runtime behavior
- move to quality when you need proof that the documented structure is still protected

## Purpose

This page explains where to look when integration behavior changes.

## Stability

Keep it aligned with real boundary modules and schema files.
