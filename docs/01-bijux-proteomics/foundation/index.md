---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Foundation

The foundation section explains why `bijux-proteomics` is split the way it is.
It is the place to resolve boundary questions before they become code drift,
docs drift, or review confusion.

The central question here is simple: why should this repository stay a package
family instead of collapsing into a blur of shared code and mixed ownership. If
that question is unresolved, the rest of the handbook will only restate the
same confusion in smaller pieces.

```mermaid
flowchart TB
    question["cross-package question"]
    platform["platform overview"]
    package["package map"]
    ownership["ownership model"]
    rules["decision rules"]
    handoff["handoff to the true owner"]

    question --> platform
    platform --> package
    package --> ownership
    ownership --> rules
    rules --> handoff
```

This section should move a reader from system-level confusion to a package-level owner without making them guess which page settles what. If the foundation pages cannot do that, the rest of the handbook only spreads the confusion into smaller fragments.

## Why This Section Matters

- it explains why the split is a quality decision, not only a packaging choice
- it gives reviewers a language for stopping ownership drift early
- it helps the reader see the family as a designed system instead of a pile of
  sibling packages

## Start With

- Open [Platform Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/platform-overview/)
  for the shortest explanation of the full package chain.
- Open [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/)
  when the question is which package should own the work.
- Open [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/)
  when a change crosses root and package boundaries.
- Open [Decision Rules](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-rules/)
  when a reviewer needs a hard yes-or-no gate.
- Open [Canonical Workflow Proof](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/canonical-workflow-proof/)
  when the question is what one real workflow family can currently prove.
- Open [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
  when the question is which workflow family a skeptical outsider can audit
  today.
- Open [Elite Readiness Scorecard](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/elite-readiness-scorecard/)
  when the question is whether repository language is outrunning public
  evidence.

## Section Pages

- [Platform Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/platform-overview/)
- [Repository Scope](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/repository-scope/)
- [Workspace Layout](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workspace-layout/)
- [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/)
- [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/)
- [Domain Language](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/domain-language/)
- [Documentation System](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/documentation-system/)
- [Change Principles](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/change-principles/)
- [Decision Rules](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-rules/)
- [Canonical Workflow Proof](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/canonical-workflow-proof/)
- [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
- [Elite Readiness Scorecard](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/elite-readiness-scorecard/)

## What This Section Settles

- why one concern becomes a package boundary while another stays local
- how package seams protect meaning, reviewability, and change control
- when a reader should stop using repository-level theory and move to a package
  handbook

## First Proof Check

- `packages/` for the actual ownership seams
- `docs/` for the handbook split mirroring those seams
- root process surfaces such as `Makefile`, `makes/`, and `apis/` when a claim
  truly sits above one package

## Design Pressure

The easy failure is to keep the root foundation section descriptive but not decisive, which leaves readers with theory and no reliable route to the real owner.

## Boundary

If the answer depends mostly on one package's source tree, tests, or public
contracts, the root foundation section should hand the reader off instead of
stretching repository prose to cover package-local behavior.
