---
title: Architecture
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Architecture

This section explains how `agentic_proteins` is organized so a reviewer can follow structure, dependency direction, and execution flow without guessing.

These pages turn `agentic-proteins` from a directory tree into a readable design map. Use them when a structural change needs to be grounded in named modules and real execution paths.

Treat the architecture pages for `agentic-proteins` as a reviewer-facing map of structure and flow. They should shorten code reading, not try to replace it.

## Visual Summary

```mermaid
flowchart LR
    page["Architecture<br/>clarifies: trace execution | spot dependency pressure | judge structural drift"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    module1["execution lifecycle and orchestration flows"]
    module1 --> page
    module2["state, memory, and artifact continuity"]
    module2 --> page
    module3["contract and schema protection across API and tools"]
    module3 --> page
    code1["src/agentic_proteins/execution and src/agentic_proteins/design_loop"]
    page --> code1
    code2["src/agentic_proteins/runtime, src/agentic_proteins/state, src/agentic_proteins/memory"]
    page --> code2
    code3["src/agentic_proteins/core, src/agentic_proteins/api, src/agentic_proteins/interfaces"]
    page --> code3
    pressure1["tests/api and tests/integration for contract and boundary behavior"]
    pressure1 -.tests whether this structure still holds.-> page
    pressure2["tests/e2e for governed flow behavior"]
    pressure2 -.tests whether this structure still holds.-> page
    pressure3["tests/regression for drift detection across execution and memory behavior"]
    pressure3 -.tests whether this structure still holds.-> page
    class page page;
    class module1,module2,module3 positive;
    class code1,code2,code3 anchor;
    class pressure1,pressure2,pressure3 caution;
```

## Pages in This Section

- [Module Map](module-map.md)
- [Dependency Direction](dependency-direction.md)
- [Execution Model](execution-model.md)
- [State and Persistence](state-and-persistence.md)
- [Integration Seams](integration-seams.md)
- [Error Model](error-model.md)
- [Extensibility Model](extensibility-model.md)
- [Code Navigation](code-navigation.md)
- [Architecture Risks](architecture-risks.md)

## Read Across the Package

- [Foundation](../foundation/index.md) when you need the package boundary and ownership story first
- [Interfaces](../interfaces/index.md) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](../quality/index.md) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `src/agentic_proteins/execution` and `src/agentic_proteins/design_loop` for lifecycle and loop orchestration
- `src/agentic_proteins/runtime`, `src/agentic_proteins/state`, and `src/agentic_proteins/memory` for continuity and persistence
- `src/agentic_proteins/core`, `src/agentic_proteins/api`, and `src/agentic_proteins/interfaces` for contracts and entry surfaces

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Architecture` to decide whether a structural change makes `agentic-proteins` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

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

This page explains how to use the architecture section for `agentic-proteins` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
