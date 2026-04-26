---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-04
---

# State and Persistence

State in `bijux-proteomics-intelligence` should be explicit enough that a maintainer can say what is
transient, what is serialized, and what neighboring packages must not assume.

That clarity matters because state tends to spread silently when it is not named.
Once readers stop knowing which outputs are durable and which values are local,
interface and operations pages quickly become less trustworthy.

Treat the architecture pages for `bijux-proteomics-intelligence` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart TB
    page["State and Persistence<br/>clarifies: trace execution | spot dependency pressure | judge structural drift"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    module1["durable runtime models"]
    module1 --> page
    module2["execution engines and lifecycle logic"]
    module2 --> page
    module3["orchestration and replay coordination"]
    module3 --> page
    code1["src/bijux_proteomics_intelligence/runtime"]
    page --> code1
    code2["src/bijux_proteomics_intelligence/application"]
    page --> code2
    code3["src/bijux_proteomics_intelligence/model"]
    page --> code3
    pressure1["tests/e2e for governed flow behavior"]
    pressure1 -.tests whether this structure still holds.-> page
    pressure2["tests/regression and tests/smoke for replay and storage protection"]
    pressure2 -.tests whether this structure still holds.-> page
    pressure3["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    pressure3 -.tests whether this structure still holds.-> page
    class page page;
    class module1,module2,module3 positive;
    class code1,code2,code3 anchor;
    class pressure1,pressure2,pressure3 caution;
```

## Durable Surfaces

- execution store records
- replay decision artifacts
- non-determinism policy evaluations

## Code Areas to Inspect

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

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `State and Persistence` to decide whether a structural change makes `bijux-proteomics-intelligence` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

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

This page marks the package's state and artifact boundary.

## Stability

Keep it aligned with the actual artifact shapes and serialized outputs.
