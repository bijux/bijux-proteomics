---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

Extension work should use the package seams that already exist instead of bypassing ownership.

This page is about where variation is welcomed and where it would be a design
smell. A package becomes easier to extend when contributors can see which seams
are meant to flex and which ones are carrying the core identity of the package.

Read the architecture pages as a reviewer-facing map of structure and flow for
`bijux-proteomics-knowledge`. They shorten code reading without trying to
replace it.

## Visual Summary

```mermaid
flowchart LR
    guard1["keep evidence inspectable"]
    guard2["separate facts from policy"]
    guard3["treat trust drift seriously"]
    page["bijux-proteomics-knowledge<br/>extensibility model"]
    ext1["new module"]
    ext2["new policy hook"]
    ext3["new integration seam"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    ext1 --> page
    ext2 --> page
    ext3 --> page
    page --> guard1
    page --> guard2
    page --> guard3
    class page page;
    class ext1,ext2,ext3 anchor;
    class guard1,guard2,guard3 action;
```

## Likely Extension Areas

- `src/bijux_proteomics_knowledge/model` for durable runtime models
- `src/bijux_proteomics_knowledge/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_knowledge/application` for orchestration and replay coordination
- `src/bijux_proteomics_knowledge/verification` for runtime-level validation support
- `src/bijux_proteomics_knowledge/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_knowledge/api` for HTTP application surfaces

## Extension Rule

Add extension points where the package already expects variation, and document them next to the owning boundary.

## Concrete Anchors

- `src/bijux_proteomics_knowledge/model` for durable runtime models
- `src/bijux_proteomics_knowledge/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_knowledge/application` for orchestration and replay coordination

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Extensibility Model` to decide whether a structural change makes `bijux-proteomics-knowledge` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-knowledge` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-knowledge`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

## Purpose

This page helps maintainers extend the package without smearing responsibilities together.

## Stability

Keep it aligned with the package seams that actually support extension today.
