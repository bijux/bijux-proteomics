---
title: Architecture
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Architecture

This section explains how `agentic_proteins` is organized as a compatibility
bridge so a reviewer can follow forwarding structure, dependency pressure, and
migration-safe execution flow without guessing.

These pages turn `agentic-proteins` from a legacy directory tree into a
readable migration map. Use them when a structural change needs to be grounded
in named forwarding surfaces and real handoffs to canonical runtime code.

The point of this section is not to glorify the legacy architecture. It is to
make the remaining bridge explicit enough that readers can tell which structure
still matters and which structure is only being tolerated until migration ends.

## Visual Summary

```mermaid
flowchart LR
    m1["forwarding import surface"]
    m2["legacy CLI bridge"]
    m3["compatibility verification"]
    section["Architecture section<br/>structure and execution map"]
    next1["module map"]
    next2["execution and seams"]
    next3["risks and navigation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    m1 --> section
    m2 --> section
    m3 --> section
    section --> next1
    section --> next2
    section --> next3
    class section page;
    class m1,m2,m3 positive;
    class next1,next2,next3 anchor;
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

## Use This Section When

- you need to understand how legacy imports and CLI paths still forward through
  the compatibility package
- you are checking whether a structural change preserves a safe migration handoff
- you need to see where the bridge structure creates review risk

## Do Not Use This Section When

- the real concern is the canonical runtime architecture rather than the legacy
  forwarding shape
- you are treating the compatibility package as a preferred place for new
  structure
- the question is about product semantics rather than forwarding seams

## Reader Takeaway

This section should help readers trace the remaining bridge structure quickly.
If a change makes the compatibility architecture more complex without making the
migration safer, that is usually a sign the work belongs elsewhere.

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
