---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-04
---

# Code Navigation

When you need to understand a change in `bijux-proteomics-knowledge`, use this reading order:

This page is intentionally practical. Its purpose is to shorten the path from a
question in review to the files that actually explain the answer.

Treat the architecture pages for `bijux-proteomics-knowledge` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart RL
    page["Code Navigation<br/>clarifies: trace execution | spot dependency pressure | judge structural drift"]
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
    code1["src/bijux_proteomics_knowledge/runtime"]
    page --> code1
    code2["src/bijux_proteomics_knowledge/application"]
    page --> code2
    code3["src/bijux_proteomics_knowledge/model"]
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

## Reading Order

- start at the relevant interface or API module
- move into the owning application or domain module
- finish in the tests that protect the behavior

## Concrete Anchors

- `src/bijux_proteomics_knowledge/model` for durable runtime models
- `src/bijux_proteomics_knowledge/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_knowledge/application` for orchestration and replay coordination
- `src/bijux_proteomics_knowledge/verification` for runtime-level validation support
- `src/bijux_proteomics_knowledge/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_knowledge/api` for HTTP application surfaces

## Test Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- tests/regression and tests/smoke for replay and storage protection
- tests/golden for durable example fixtures

## Concrete Anchors

- `src/bijux_proteomics_knowledge/model` for durable runtime models
- `src/bijux_proteomics_knowledge/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_knowledge/application` for orchestration and replay coordination

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Code Navigation` to decide whether a structural change makes `bijux-proteomics-knowledge` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

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

- move to interfaces when the review reaches a public or operator-facing seam
- move to operations when the concern becomes repeatable runtime behavior
- move to quality when you need proof that the documented structure is still protected

## Purpose

This page shortens the path from an issue report to the relevant code.

## Stability

Keep it aligned with the real source tree and current test layout.
