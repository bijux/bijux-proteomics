---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Foundation

`bijux-proteomics-core` exists to define durable program rules: target models,
lifecycle states, readiness conditions, and validation boundaries that the rest
of the proteomics stack has to respect. Use this section when the key question
is why a rule belongs to the core contract layer instead of a downstream policy
package.

These pages should help readers separate durable contract from flexible policy.
When this section is clear, it becomes obvious why intelligence may rank or lab
may plan differently, but neither gets to rewrite the underlying lifecycle or
program meaning on its own.

## Visual Summary

```mermaid
flowchart LR
    programs["target and program contracts"]
    lifecycle["lifecycle and readiness rules"]
    validation["deterministic validation logic"]
    contracts["durable contract layer"]
    boundary["boundary<br/>ranking and execution policy start later"]
    reader["reader question<br/>is this a core rule or downstream policy?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    programs --> contracts
    lifecycle --> contracts
    validation --> contracts
    contracts --> boundary
    contracts --> reader
    class contracts page;
    class programs,lifecycle,validation positive;
    class reader anchor;
    class boundary caution;
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest explanation of
  what the contract layer owns
- open [Ownership Boundary](ownership-boundary.md) when the issue may actually
  belong in foundation, intelligence, lab, or runtime instead
- open [Lifecycle Overview](lifecycle-overview.md) when the real question is
  how programs move through states and readiness checks

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Ownership Boundary](ownership-boundary.md)
- [Repository Fit](repository-fit.md)
- [Capability Map](capability-map.md)
- [Domain Language](domain-language.md)
- [Lifecycle Overview](lifecycle-overview.md)
- [Dependencies and Adjacencies](dependencies-and-adjacencies.md)
- [Change Principles](change-principles.md)

## Use This Section When

- you need the durable ownership story before reading code or command surfaces
- you are deciding whether a rule is part of the core contract or only a
  downstream choice
- you need the package vocabulary for programs, lifecycle transitions,
  readiness, and validation

## Do Not Use This Section When

- the question is already about commands, imports, schemas, or artifacts
- the real issue is operational, such as running validations or releasing the
  package
- you already know the boundary and need proof, risk posture, or review
  criteria instead

## Read Across The Package

- open [Architecture](../architecture/index.md) when you need the structural
  map behind program, lifecycle, and validation code
- open [Interfaces](../interfaces/index.md) when the question is about public
  contract surfaces
- open [Operations](../operations/index.md) when you need repeatable workflows
  for contract changes or validation runs
- open [Quality](../quality/index.md) when you need evidence that the durable
  contract is actually protected

## Concrete Anchors

- `packages/bijux-proteomics-core` as the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics` as the import boundary
- `packages/bijux-proteomics-core/tests` as the proof surface for contract
  behavior

## Reader Takeaway

Use `Foundation` to answer the ownership question with integrity:
`bijux-proteomics-core` exists so the rest of the proteomics stack can depend on
one stable program and lifecycle contract. If a proposal broadens this package
without making that contract story clearer, it is probably crossing the
boundary rather than improving it.

## Purpose

This page introduces the foundation handbook for `bijux-proteomics-core` and
routes readers to the boundary, language, and lifecycle pages that explain why
the package exists.
