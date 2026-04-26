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

- [Module Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/architecture-risks/)

## Open This Section When

- you need to understand how legacy imports and CLI paths still forward through
  the compatibility package
- you are checking whether a structural change preserves a safe migration handoff
- you need to see where the bridge structure creates review risk

## Open Another Section When

- the real concern is the canonical runtime architecture rather than the legacy
  forwarding shape
- you are treating the compatibility package as a preferred place for new
  structure
- the question is about product semantics rather than forwarding seams

## Reader Takeaway

This section helps readers trace the remaining bridge structure quickly.
If a change makes the compatibility architecture more complex without making the
migration safer, that is usually a sign the work belongs elsewhere.

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/) when you need the package boundary and ownership story first
- [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/) when the question becomes caller-facing, schema-facing, or contract-facing
- [Operations](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `src/agentic_proteins/execution` and `src/agentic_proteins/design_loop` for lifecycle and loop orchestration
- `src/agentic_proteins/runtime`, `src/agentic_proteins/state`, and `src/agentic_proteins/memory` for continuity and persistence
- `src/agentic_proteins/core`, `src/agentic_proteins/api`, and `src/agentic_proteins/interfaces` for contracts and entry surfaces

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Architecture` to decide whether a structural change makes `agentic-proteins` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What You Can Resolve Here

- how `agentic-proteins` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Review Focus

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Limits

This page describes the current structural model of `agentic-proteins`, but it does not guarantee that every import path or runtime path still obeys that model. Treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Read Next

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

