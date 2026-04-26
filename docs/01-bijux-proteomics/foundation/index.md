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

## Start With

- Open [Platform Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/platform-overview/)
  for the shortest explanation of the full package chain.
- Open [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/)
  when the question is which package should own the work.
- Open [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/)
  when a change crosses root and package boundaries.
- Open [Decision Rules](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-rules/)
  when a reviewer needs a hard yes-or-no gate.

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

## First Proof Check

- `packages/` for the actual ownership seams
- `docs/` for the handbook split mirroring those seams
- root process surfaces such as `Makefile`, `makes/`, and `apis/` when a claim
  truly sits above one package

## Boundary

If the answer depends mostly on one package's source tree, tests, or public
contracts, the root foundation section should hand the reader off instead of
stretching repository prose to cover package-local behavior.
