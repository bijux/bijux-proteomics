---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

The package should keep dependency direction readable: domain intent near the center,
interfaces and infrastructure at the edges.

This is not only an aesthetic preference. Clear dependency direction keeps
refactors cheaper because reviewers can still tell which layers are allowed to
know about which other layers.

Treat the architecture pages for `bijux-proteomics-intelligence` as a reviewer-facing map of structure and flow. They shorten code reading instead of trying to replace it.

## Visual Summary

```mermaid
flowchart LR
    up1["knowledge evidence state"]
    up2["core constraints"]
    up3["candidate comparisons"]
    page["bijux-proteomics-intelligence<br/>dependency direction"]
    down1["lab planning choices"]
    down2["runtime-selected paths"]
    down3["reviewer explanations"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    up1 --> page
    up2 --> page
    up3 --> page
    page --> down1
    page --> down2
    page --> down3
    class page page;
    class up1,up2,up3 anchor;
    class down1,down2,down3 positive;
```

## Directional Reading Order

- domain and model concerns under the core module groups
- application orchestration that composes domain behavior
- interfaces, APIs, and adapters that sit at the boundary

## Concrete Anchors

- `src/bijux_proteomics_intelligence/model` for durable runtime models
- `src/bijux_proteomics_intelligence/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_intelligence/application` for orchestration and replay coordination
- `src/bijux_proteomics_intelligence/verification` for runtime-level validation support
- `src/bijux_proteomics_intelligence/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_intelligence/api` for HTTP application surfaces

## Concrete Anchors

- `src/bijux_proteomics_intelligence/model` for durable runtime models
- `src/bijux_proteomics_intelligence/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_intelligence/application` for orchestration and replay coordination

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Dependency Direction` to decide whether a structural change makes `bijux-proteomics-intelligence` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-intelligence` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-intelligence`, but it does not guarantee that every import path or runtime path still obeys that model. Treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

