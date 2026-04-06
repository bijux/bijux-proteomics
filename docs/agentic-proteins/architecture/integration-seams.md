---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Integration Seams

Integration seams are the points where `agentic-proteins` meets configuration, APIs,
operators, or neighboring packages.

This page exists so integration changes do not feel mysterious. A reviewer should
be able to say which seams are intentional, which ones carry compatibility risk,
and where the package expects outside systems to meet it.

Treat the architecture pages for `agentic-proteins` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart RL
    page["Integration Seams<br/>clarifies: trace execution | spot dependency pressure | judge structural drift"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    module1["orchestration and replay coordination"]
    module1 --> page
    module2["durable runtime models"]
    module2 --> page
    module3["execution engines and lifecycle logic"]
    module3 --> page
    code1["src/agentic_proteins/runtime"]
    page --> code1
    code2["src/agentic_proteins/application"]
    page --> code2
    code3["src/agentic_proteins/model"]
    page --> code3
    pressure1["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    pressure1 -.tests whether this structure still holds.-> page
    pressure2["tests/e2e for governed flow behavior"]
    pressure2 -.tests whether this structure still holds.-> page
    pressure3["tests/regression and tests/smoke for replay and storage protection"]
    pressure3 -.tests whether this structure still holds.-> page
    class page page;
    class module1,module2,module3 positive;
    class code1,code2,code3 anchor;
    class pressure1,pressure2,pressure3 caution;
```

## Integration Surfaces

- CLI entrypoint in src/agentic_proteins/interfaces/cli/entrypoint.py
- HTTP app in src/agentic_proteins/api/v1
- schema files in api/agentic-proteins/v1

## Adjacent Systems

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `src/agentic_proteins/model` for durable runtime models
- `src/agentic_proteins/runtime` for execution engines and lifecycle logic
- `src/agentic_proteins/application` for orchestration and replay coordination

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Integration Seams` to decide whether a structural change makes `agentic-proteins` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `agentic-proteins` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `agentic-proteins`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- move to interfaces when the review reaches a public or operator-facing seam
- move to operations when the concern becomes repeatable runtime behavior
- move to quality when you need proof that the documented structure is still protected

## Purpose

This page explains where to look when integration behavior changes.

## Stability

Keep it aligned with real boundary modules and schema files.
