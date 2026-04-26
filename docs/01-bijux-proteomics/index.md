---
title: Repository Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Repository Handbook

The repository handbook exists for questions that no single package can answer
honestly on its own. It explains why the proteomics system is split, which
assets genuinely live above one package boundary, and where repository authority
must stop before it starts swallowing package behavior.

That boundary is the point of the root. If one package can explain the behavior
fully, the reader should leave the repository handbook and use the owning
package docs instead of treating the root as a catch-all explanation layer.

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/)
  when the question is why the split exists or where authority changes hands.
- Open [Operations](https://bijux.io/bijux-proteomics/01-bijux-proteomics/operations/)
  when the question is about repository-wide validation, release, review, or
  shared automation.
- Open the [Maintainer Handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
  when the issue is implemented as helper code, make routing, or workflow
  automation.

## What The Root Owns

- cross-package boundary rules and handoff logic
- repository-wide workflow, validation, release, and artifact discipline
- shared docs structure and other assets that sit above one package

## What The Root Refuses

- runtime execution behavior that belongs in `bijux-proteomics-runtime`
- domain, evidence, scoring, or lab semantics that belong in product packages
- maintainer implementation detail that belongs in `bijux-proteomics-dev`

## Product Handbooks

- [agentic-proteins](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
- [bijux-proteomics-foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
- [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
- [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
- [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
- [bijux-proteomics-lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
- [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)

## First Proof Check

- `packages/` for the package seams this handbook is describing
- `Makefile` and `makes/` for root-owned command and release routing
- `apis/` and `.github/workflows/` for repository-level contract and validation
  surfaces

## Boundary Test

If the best proof lives mostly in one package source tree, one package test
suite, or one package API contract, the root should hand the reader off instead
of pretending repository prose owns that behavior.
