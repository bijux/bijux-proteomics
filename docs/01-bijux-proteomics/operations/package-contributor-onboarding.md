---
title: Package Contributor Onboarding
audience: contributor
type: guide
status: canonical
owner: bijux-proteomics-dev
last_reviewed: 2026-04-29
---

# Package Contributor Onboarding

Use this page when a contributor is new to the package family and needs the shortest honest path to the right package, docs, and tests.

## First Moves

1. start with the repository handbook and the target package `README.md` before editing code
2. open the package docs root and package tests before inventing a new pattern
3. check direct workspace dependencies so boundary pressure is visible before implementation

## Package Map

| package | distribution | import root | direct workspace dependencies | read first | tests | docs |
| --- | --- | --- | --- | --- | --- | --- |
| `agentic-proteins` | `agentic-proteins` | `agentic_proteins` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-intelligence`, `bijux-proteomics-knowledge`, `bijux-proteomics-lab`, `bijux-proteomics-runtime` | `packages/agentic-proteins/README.md` | `packages/agentic-proteins/tests` | `docs/02-agentic-proteins` |
| `bijux-proteomics-dev` | `bijux-proteomics-dev` | `bijux_proteomics_dev` | `agentic-proteins` | `packages/bijux-proteomics-dev/README.md` | `packages/bijux-proteomics-dev/tests` | `docs/08-bijux-proteomics-maintain/bijux-proteomics-dev` |
| `bijux-proteomics-foundation` | `bijux-proteomics-foundation` | `bijux_proteomics_foundation` | _none_ | `packages/bijux-proteomics-foundation/README.md` | `packages/bijux-proteomics-foundation/tests` | `docs/03-bijux-proteomics-foundation` |
| `bijux-proteomics-core` | `bijux-proteomics-core` | `bijux_proteomics` | `bijux-proteomics-foundation` | `packages/bijux-proteomics-core/README.md` | `packages/bijux-proteomics-core/tests` | `docs/04-bijux-proteomics-core` |
| `bijux-proteomics-runtime` | `bijux-proteomics-runtime` | `bijux_proteomics_runtime` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-intelligence`, `bijux-proteomics-knowledge`, `bijux-proteomics-lab` | `packages/bijux-proteomics-runtime/README.md` | `packages/bijux-proteomics-runtime/tests` | `docs/09-bijux-proteomics-runtime` |
| `bijux-proteomics-intelligence` | `bijux-proteomics-intelligence` | `bijux_proteomics_intelligence` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-knowledge` | `packages/bijux-proteomics-intelligence/README.md` | `packages/bijux-proteomics-intelligence/tests` | `docs/05-bijux-proteomics-intelligence` |
| `bijux-proteomics-knowledge` | `bijux-proteomics-knowledge` | `bijux_proteomics_knowledge` | `bijux-proteomics-foundation` | `packages/bijux-proteomics-knowledge/README.md` | `packages/bijux-proteomics-knowledge/tests` | `docs/06-bijux-proteomics-knowledge` |
| `bijux-proteomics-lab` | `bijux-proteomics-lab` | `bijux_proteomics_lab` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-knowledge` | `packages/bijux-proteomics-lab/README.md` | `packages/bijux-proteomics-lab/tests` | `docs/07-bijux-proteomics-lab` |

## Reading Order

- choose `bijux-proteomics-dev` for repo policy, docs integrity, release validation, and package boundary checks
- choose `bijux-proteomics-core` for scientific contracts and stable proteomics model behavior
- choose `bijux-proteomics-runtime` only when the concern is orchestration, replay, or execution control
- treat `agentic-proteins` as compatibility stewardship, not a place for new product growth
