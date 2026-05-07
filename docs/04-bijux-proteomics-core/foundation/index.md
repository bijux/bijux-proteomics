---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Foundation

The foundation section explains the durable role of `bijux-proteomics-core` before it
explains implementation detail. Use it to resolve why durable workflow rules belong here before evidence, scoring, or execution layers act on them.

```mermaid
flowchart LR
    lifecycle["lifecycle states"]
    gates["gate semantics"]
    workflows["workflow contracts"]
    core["core foundation"]
    intelligence["intelligence"]
    runtime["runtime"]
    lab["lab"]

    lifecycle --> core
    gates --> core
    workflows --> core
    core --> intelligence
    core --> runtime
    core --> lab
```

## What This Section Protects

- one durable grammar for workflows before downstream packages optimize around
  it
- gate semantics that remain reviewable instead of dissolving into code paths
- lifecycle discipline that survives changes in policy or execution tooling

## Start With

- Open [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/) for the shortest statement of
  the package role.
- Open [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/) when the question is
  whether a change belongs here or in a neighbor.
- Open [Scope and Non-Goals](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/scope-and-non-goals/) when a proposed change
  risks broadening the package.
- Open [Capability Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/capability-map/) when you need the concrete work
  the package is allowed to do.
- Open [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
  when you need the current public package roots and artifact contracts across
  the flagship workflow families.

## Section Pages

- [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- [Capability Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/capability-map/)
- [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dependencies-and-adjacencies/)
- [Repository Fit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/repository-fit/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lifecycle-overview/)
- [Domain Language](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/domain-language/)
- [Change Principles](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/change-principles/)

## What This Section Settles

- when a rule is foundational enough to belong in core
- how much downstream freedom exists once lifecycle and gate contracts are set
- when a proposed change is really policy or execution and should leave this
  package

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- neighboring handbooks once the change crosses the local boundary

## Neighbors

- Open [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
  when the question leaves program contracts, lifecycle rules, and gate semantics.
- Open [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
  when the issue is clearly outside this package's local role.
