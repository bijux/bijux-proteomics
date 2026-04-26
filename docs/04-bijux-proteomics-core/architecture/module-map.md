---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Module Map

The architecture of `bijux-proteomics-core` becomes readable when its major module
groups are treated as responsibilities instead of as folders. This page helps a
reviewer move from a question about behavior to the part of the package most
likely to answer it.

When this page is useful, code reading becomes targeted rather than exploratory.

Read the architecture pages as a reviewer-facing map of structure and flow for
`bijux-proteomics-core`. They shorten code reading without trying to replace it.

## Visual Summary

```mermaid
flowchart LR
    m1["program models"]
    m2["lifecycle validation"]
    m3["contract evaluation"]
    page["bijux-proteomics-core<br/>major module groups"]
    code1["src/bijux_proteomics_core"]
    code2["tests"]
    code3["docs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    m1 --> page
    m2 --> page
    m3 --> page
    page --> code1
    page --> code2
    page --> code3
    class page page;
    class m1,m2,m3 positive;
    class code1,code2,code3 anchor;
```

## Major Modules

- `src/bijux_proteomics/model` for durable runtime models
- `src/bijux_proteomics/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics/application` for orchestration and replay coordination
- `src/bijux_proteomics/verification` for runtime-level validation support
- `src/bijux_proteomics/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics/api` for HTTP application surfaces

## Concrete Anchors

- `src/bijux_proteomics/model` for durable runtime models
- `src/bijux_proteomics/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics/application` for orchestration and replay coordination

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Module Map` to decide whether a structural change makes `bijux-proteomics-core` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What You Can Resolve Here

- how `bijux-proteomics-core` is organized internally in terms a reviewer can follow
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

