---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams are the points where `agentic-proteins` meets configuration, APIs,
operators, or neighboring packages.

This page makes integration changes easier to review by showing which seams are intentional, which ones carry compatibility risk, and where the package expects outside systems to meet it.

This page is a reviewer-facing map of structure and flow. It shortens code reading instead of trying to replace it.

## Visual Summary

```mermaid
flowchart LR
    seam1["runtime forwarding seam"]
    seam2["legacy caller expectations"]
    seam3["repository release rules"]
    page["agentic-proteins<br/>integration seams"]
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

- CLI entrypoint in src/agentic_proteins/interfaces/cli.py
- HTTP app in src/agentic_proteins/api/v1
- shared API schema in apis/agentic-proteins/v1

## Adjacent Systems

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `src/agentic_proteins/model` for durable runtime models
- `src/agentic_proteins/runtime` for execution engines and lifecycle logic
- `src/agentic_proteins/application` for orchestration and replay coordination

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Integration Seams` to decide whether a structural change makes `agentic-proteins` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What You Can Resolve Here

- how `agentic-proteins` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Review Focus

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Limits

Treat this page as a working structural map and keep it aligned with code and tests.

## Read Next

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

