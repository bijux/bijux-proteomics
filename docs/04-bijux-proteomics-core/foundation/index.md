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
of the proteomics stack has to respect. Open this section when the key question
is why a rule belongs to the core contract layer instead of a downstream policy
package.

These pages should help readers separate durable contract from flexible policy.
When this section is clear, it becomes obvious why intelligence may rank or lab
may plan differently, but neither gets to rewrite the underlying lifecycle or
program meaning on its own.

## Start Here

- open [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/) for the shortest explanation of
  what the contract layer owns
- open [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/) when the issue may actually
  belong in foundation, intelligence, lab, or runtime instead
- open [Lifecycle Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lifecycle-overview/) when the real question is
  how programs move through states and readiness checks

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/change-principles/)

## Open This Section When

- you need the durable ownership story before reading code or command surfaces
- you are deciding whether a rule is part of the core contract or only a
  downstream choice
- you need the package vocabulary for programs, lifecycle transitions,
  readiness, and validation

## Open Another Section When

- the question is already about commands, imports, schemas, or artifacts
- the real issue is operational, such as running validations or releasing the
  package
- you already know the boundary and need proof, risk posture, or review
  criteria instead

## Read Across The Package

- open [Architecture](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/) when you need the structural
  map behind program, lifecycle, and validation code
- open [Interfaces](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/) when the question is about public
  contract surfaces
- open [Operations](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/) when you need repeatable workflows
  for contract changes or validation runs
- open [Quality](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/quality/) when you need evidence that the durable
  contract is actually protected

## Concrete Anchors

- `packages/bijux-proteomics-core` as the package root
- `packages/bijux-proteomics-core/src/bijux_proteomics` as the import boundary
- `packages/bijux-proteomics-core/tests` as the proof surface for contract
  behavior

## Bottom Line

Use `Foundation` to answer the ownership question with integrity:
`bijux-proteomics-core` exists so the rest of the proteomics stack can depend on
one stable program and lifecycle contract. If a proposal broadens this package
without making that contract story clearer, it is probably crossing the
boundary rather than improving it.

