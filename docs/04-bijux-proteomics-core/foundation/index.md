---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Foundation

The core foundation section is where the repository names its durable
scientific law: workflow contracts, lifecycle transitions, review gates,
runtime-agnostic request shapes, and benchmark acceptance logic. If a page here
needs recommendation posture or operator transport to justify itself, the
boundary is already drifting.

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

- one canonical workflow grammar before downstream packages add policy or
  transport
- review-gate and lifecycle truth that stays inspectable outside runtime code
- scientific contracts that remain distinct from evidence memory and lab burden

## Start With

- Open [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/) for the shortest statement of
  the package role.
- Open [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/) when the question is
  whether a change belongs here or in a neighbor.
- Open [This Package Does Not Own](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/this-package-does-not-own/)
  when the question is whether a proposal is trying to push evidence,
  recommendation, or execution delivery back into core.
- Open [Scope and Non-Goals](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/scope-and-non-goals/) when a proposed change
  risks broadening the package.
- Open [Capability Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/capability-map/) when you need the concrete work
  the package is allowed to do.
- Open [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
  when you need the current public package roots and artifact contracts across
  the flagship workflow families.
- Open [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
  when you need the copied-source contract, rebuild command, citation manifest,
  freshness report, and obsolescence audit behind those roots.
- Open [Benchmark Asset Audit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-asset-audit/)
  when you need every primary and companion benchmark root re-audited for raw
  source, checksum, extraction step, derived review path, and owning rebuild
  command.
- Open [Benchmark Freshness Review](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-freshness-review/)
  when the question is whether a workflow family's benchmark review window,
  copied snapshots, or remote references have slipped far enough to narrow
  release language.
- Open the family lineage pages when the dispute is whether one workflow family
  still holds together across both its primary flagship package and its
  companion generalization package.
- Open [Benchmark Licensing and Redistribution](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-licensing-and-redistribution/)
  when the question is what the repository redistributes as governed evidence
  versus what remains only a public reference or external-engine context.
- Open [Benchmark Incompleteness Ledger](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-incompleteness-ledger/)
  when you need the live blockers, realism limits, non-transfer zones, and
  failure conditions that still cap benchmark trust.
- Open [Benchmark Flagship Status](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-flagship-status/)
  when the question is whether a package root still deserves flagship naming or
  should be treated only as a companion or internal-support surface.
- Open [Flagship Challenge Corpus Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-challenge-corpus-catalog/)
  when you need the blinded holdouts and perturbation roots that deliberately
  try to break those benchmark claims.
- Open [Flagship Acceptance Bars](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-acceptance-bars/)
  when you need the exact thresholds, dashboard, history ledger, and rationale
  dossier that decide whether release trust is still earned.

## Section Pages

- [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- [This Package Does Not Own](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/this-package-does-not-own/)
- [Capability Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/capability-map/)
- [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
- [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
- [Benchmark Asset Audit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-asset-audit/)
- [Benchmark Freshness Review](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-freshness-review/)
- [Benchmark Licensing and Redistribution](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-licensing-and-redistribution/)
- [Benchmark Incompleteness Ledger](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-incompleteness-ledger/)
- [Benchmark Flagship Status](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-flagship-status/)
- [DDA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dda-benchmark-lineage/)
- [DIA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dia-benchmark-lineage/)
- [LFQ Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lfq-benchmark-lineage/)
- [Multiplex Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/multiplex-benchmark-lineage/)
- [PTM Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ptm-benchmark-lineage/)
- [Targeted Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/targeted-benchmark-lineage/)
- [Flagship Challenge Corpus Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-challenge-corpus-catalog/)
- [Flagship Acceptance Bars](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-acceptance-bars/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dependencies-and-adjacencies/)
- [Repository Fit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/repository-fit/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lifecycle-overview/)
- [Domain Language](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/domain-language/)
- [Change Principles](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/change-principles/)

## What This Section Settles

- whether a rule changes canonical scientific workflow truth or only downstream
  interpretation
- which benchmark-acceptance and lifecycle surfaces are still owned here
- when a proposed change is really evidence policy, runtime delivery, or lab
  consequence and should leave this package

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- neighboring handbooks once the change crosses the local boundary

## Neighbors

- Open [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
  when the question leaves program contracts, lifecycle rules, and gate semantics.
- Open [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
  when the issue is clearly outside this package's local role.
