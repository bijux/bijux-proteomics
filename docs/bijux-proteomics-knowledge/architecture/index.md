---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-04
---

# Architecture

This section maps the real module layout for `bijux-proteomics-knowledge`.

The package is not split into `runtime/model/application` layers. The structure
is feature-oriented around evidence, claims, conflict resolution, review, and
graph semantics.

## Visual Summary

```mermaid
flowchart LR
    evidence["evidence.py"]
    claims["claims.py"]
    resolution["resolution.py"]
    review["review.py"]
    graph["graph.py"]
    repositories["repositories.py"]
    adapters["adapters.py"]
    evidence --> claims
    claims --> resolution
    resolution --> review
    claims --> graph
    repositories --> review
    adapters --> evidence
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

- `src/bijux_proteomics_knowledge/evidence.py` for evidence modeling and trust logic
- `src/bijux_proteomics_knowledge/claims.py` for claim lifecycle and lineage behavior
- `src/bijux_proteomics_knowledge/resolution.py` for conflict resolution policy behavior
- `src/bijux_proteomics_knowledge/review.py` for review-packet and readiness summarization

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Architecture` to decide whether a structural change makes `bijux-proteomics-knowledge` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how the package is actually decomposed today
- which modules are core dependency hubs
- where structural drift is likely to create caller confusion

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

This page explains how to use the architecture section for `bijux-proteomics-knowledge` without repeating the detail that belongs on the topic pages beneath it.

## Stability

This page is part of the canonical package docs spine. Keep it aligned with the current package boundary and the topic pages in this section.
