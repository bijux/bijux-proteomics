---
title: bijux-proteomics-core
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-core

`bijux-proteomics-core` is the program contract package in
`bijux-proteomics`. Start here when the question is about target
programs, gate definitions, lifecycle states, readiness rules, and the
cross-package contracts that higher layers must respect.

This section should make one boundary obvious: core defines the durable
program and lifecycle rules, but it does not own evidence policy,
scoring policy, or lab execution details.

## Visual Summary

```mermaid
flowchart LR
    programs["target programs<br/>and gate models"]
    lifecycle["lifecycle states<br/>and readiness rules"]
    validation["deterministic contract<br/>validation"]
    core["bijux-proteomics-core<br/>program contract layer"]
    knowledge["knowledge uses core states"]
    intelligence["intelligence ranks within core rules"]
    lab["lab plans under core constraints"]
    runtime["runtime executes against core contracts"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    programs --> core
    lifecycle --> core
    validation --> core
    core --> knowledge
    core --> intelligence
    core --> lab
    core --> runtime
    class core page;
    class knowledge,intelligence,lab,runtime positive;
    class programs,lifecycle,validation anchor;
```

## Read This Section When

- you need the package entrypoint for program and gate contracts
- you are checking lifecycle transitions, identifiers, or readiness validation
- you want the shortest route into durable program semantics

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-foundation](../03-bijux-proteomics-foundation/index.md) when shared payload meaning is the real issue
- move to [bijux-proteomics-intelligence](../05-bijux-proteomics-intelligence/index.md) when the question becomes ranking or recommendation policy
- stay here when you need to know whether a rule is part of the durable contract or just a downstream policy choice

## Concrete Anchors

- `packages/bijux-proteomics-core` for the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics_core` for contract ownership
- `packages/bijux-proteomics-core/tests` for program and lifecycle proof

## Purpose

This page gives readers the shortest honest route into the contract layer
that the rest of the proteomics stack builds on.

## Stability

Keep it aligned with the lifecycle, gate, and readiness contracts that
downstream packages must obey.
