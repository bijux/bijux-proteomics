---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-04
---

# Dependency Direction

The package should keep dependency direction readable: domain intent near the center,
interfaces and infrastructure at the edges.

This is not only an aesthetic preference. Clear dependency direction keeps
refactors cheaper because reviewers can still tell which layers are allowed to
know about which other layers.

Treat the architecture pages for `bijux-proteomics-lab` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart TB
    page["Dependency Direction<br/>clarifies: trace execution | spot dependency pressure | judge structural drift"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    module1["durable runtime models"]
    module1 --> page
    module2["execution engines and lifecycle logic"]
    module2 --> page
    module3["orchestration and replay coordination"]
    module3 --> page
    code1["src/bijux_proteomics_lab/runtime"]
    page --> code1
    code2["src/bijux_proteomics_lab/application"]
    page --> code2
    code3["src/bijux_proteomics_lab/model"]
    page --> code3
    pressure1["tests/regression and tests/smoke for replay and storage protection"]
    pressure1 -.tests whether this structure still holds.-> page
    pressure2["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    pressure2 -.tests whether this structure still holds.-> page
    pressure3["tests/e2e for governed flow behavior"]
    pressure3 -.tests whether this structure still holds.-> page
    class page page;
    class module1,module2,module3 positive;
    class code1,code2,code3 anchor;
    class pressure1,pressure2,pressure3 caution;
```

## Directional Reading Order

- domain and model concerns under the core module groups
- application orchestration that composes domain behavior
- interfaces, APIs, and adapters that sit at the boundary

## Concrete Anchors

- `src/bijux_proteomics_lab/model` for durable runtime models
- `src/bijux_proteomics_lab/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_lab/application` for orchestration and replay coordination
- `src/bijux_proteomics_lab/verification` for runtime-level validation support
- `src/bijux_proteomics_lab/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_lab/api` for HTTP application surfaces

## Concrete Anchors

- `src/bijux_proteomics_lab/model` for durable runtime models
- `src/bijux_proteomics_lab/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_lab/application` for orchestration and replay coordination

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Dependency Direction` to decide whether a structural change makes `bijux-proteomics-lab` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-lab` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-lab`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- move to interfaces when the review reaches a public or operator-facing seam
- move to operations when the concern becomes repeatable runtime behavior
- move to quality when you need proof that the documented structure is still protected

## Purpose

This page makes dependency direction explicit enough to review during refactors.

## Stability

Keep it aligned with current imports and directory responsibilities.
