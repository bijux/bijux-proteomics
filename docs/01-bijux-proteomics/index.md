---
title: Repository Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Handbook

Open this handbook for questions that no single package can answer on its own.
The root is not a sixth product package. It explains how the package family
fits together, which assets genuinely live above one package, and where
cross-package rules begin and end.

If a reader can answer their question honestly from one package handbook, they
should go there instead of staying here.

The root coordinates package boundaries, shared repository rules, and
cross-package handoffs. It should explain how the package family fits together
without quietly absorbing domain, runtime, or lab semantics that belong
elsewhere.

## Start Here

- open [Foundation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/) when the question is why the package
  split exists or where authority changes hands
- open [Operations](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/) when the question is how repository
  work is validated, released, or reviewed
- open a product handbook when the real issue is already local to one package
  boundary
- open the [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/) when
  the concern is CI, workflow fan-out, generated docs checks, or release
  tooling

## Pages In This Handbook

- [Foundation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/)
- [Operations](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/)

## What This Handbook Owns

- the shared explanation of why the root exists at all
- repository-wide workflow, validation, release, and artifact rules
- the seams where one package hands responsibility to another

## What This Handbook Does Not Own

- runtime execution behavior, provider semantics, or replay authority
- foundation, core, intelligence, knowledge, or lab behavior inside those
  package docs
- maintainer-helper implementation detail that belongs in the maintainer
  handbook

## Open This Handbook When

- questions about why the repository is split the way it is
- questions about root-managed assets such as `apis/`, `Makefile`, shared CI,
  and release conventions
- questions about where the root should stop and a product package should take
  over

## Open Another Handbook When

- the answer lives mostly in one package's source tree, tests, or public
  surface
- the question is about one package's internal boundary rather than repository
  fit
- you are tempted to describe behavior at the root that really belongs inside
  `packages/`

## Package Handbooks

- [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/)
- [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/)
- [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/)
- [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/)
- [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/)
- [bijux-proteomics-lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/)

## Concrete Anchors

- `pyproject.toml` for workspace metadata and package declarations
- `Makefile` and `makes/` for root automation and release routing
- `apis/` and `.github/workflows/` for schema and validation review
- `packages/` for the product boundaries this handbook must not blur

## Bottom Line

Open this handbook to choose the right package or repository-level surface. If
one product handbook can answer the question honestly, leave the root and use
that handbook.
