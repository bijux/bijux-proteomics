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
| `agentic-proteins` | `agentic-proteins` | `agentic_proteins` | `bijux-proteomics-core`, `bijux-proteomics-runtime` | `packages/agentic-proteins/README.md` | `packages/agentic-proteins/tests` | `docs/02-agentic-proteins` |
| `bijux-proteomics-dev` | `bijux-proteomics-dev` | `bijux_proteomics_dev` | `agentic-proteins` | `packages/bijux-proteomics-dev/README.md` | `packages/bijux-proteomics-dev/tests` | `docs/08-bijux-proteomics-maintain/bijux-proteomics-dev` |
| `bijux-proteomics-foundation` | `bijux-proteomics-foundation` | `bijux_proteomics_foundation` | _none_ | `packages/bijux-proteomics-foundation/README.md` | `packages/bijux-proteomics-foundation/tests` | `docs/03-bijux-proteomics-foundation` |
| `bijux-proteomics-core` | `bijux-proteomics-core` | `bijux_proteomics` | `bijux-proteomics-foundation` | `packages/bijux-proteomics-core/README.md` | `packages/bijux-proteomics-core/tests` | `docs/04-bijux-proteomics-core` |
| `bijux-proteomics-runtime` | `bijux-proteomics-runtime` | `bijux_proteomics_runtime` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-intelligence`, `bijux-proteomics-knowledge`, `bijux-proteomics-lab` | `packages/bijux-proteomics-runtime/README.md` | `packages/bijux-proteomics-runtime/tests` | `docs/09-bijux-proteomics-runtime` |
| `bijux-proteomics-intelligence` | `bijux-proteomics-intelligence` | `bijux_proteomics_intelligence` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-knowledge` | `packages/bijux-proteomics-intelligence/README.md` | `packages/bijux-proteomics-intelligence/tests` | `docs/05-bijux-proteomics-intelligence` |
| `bijux-proteomics-knowledge` | `bijux-proteomics-knowledge` | `bijux_proteomics_knowledge` | `bijux-proteomics-foundation` | `packages/bijux-proteomics-knowledge/README.md` | `packages/bijux-proteomics-knowledge/tests` | `docs/06-bijux-proteomics-knowledge` |
| `bijux-proteomics-lab` | `bijux-proteomics-lab` | `bijux_proteomics_lab` | `bijux-proteomics-core`, `bijux-proteomics-foundation`, `bijux-proteomics-knowledge` | `packages/bijux-proteomics-lab/README.md` | `packages/bijux-proteomics-lab/tests` | `docs/07-bijux-proteomics-lab` |
| `bijux-proteomics` | `bijux-proteomics` | `bijux_proteomics_alias` | `bijux-proteomics-core` | `packages/bijux-proteomics/README.md` | `packages/bijux-proteomics/tests` | `docs/01-bijux-proteomics` |
| `proteomics` | `proteomics` | `proteomics` | `bijux-proteomics-core` | `packages/proteomics/README.md` | `packages/proteomics/tests` | `docs/01-bijux-proteomics` |
| `proteomics-core` | `proteomics-core` | `proteomics_core` | `bijux-proteomics-core` | `packages/proteomics-core/README.md` | `packages/proteomics-core/tests` | `docs/04-bijux-proteomics-core` |
| `proteomics-foundation` | `proteomics-foundation` | `proteomics_foundation` | `bijux-proteomics-foundation` | `packages/proteomics-foundation/README.md` | `packages/proteomics-foundation/tests` | `docs/03-bijux-proteomics-foundation` |
| `proteomics-runtime` | `proteomics-runtime` | `proteomics_runtime` | `bijux-proteomics-runtime` | `packages/proteomics-runtime/README.md` | `packages/proteomics-runtime/tests` | `docs/09-bijux-proteomics-runtime` |
| `proteomics-intelligence` | `proteomics-intelligence` | `proteomics_intelligence` | `bijux-proteomics-intelligence` | `packages/proteomics-intelligence/README.md` | `packages/proteomics-intelligence/tests` | `docs/05-bijux-proteomics-intelligence` |
| `proteomics-knowledge` | `proteomics-knowledge` | `proteomics_knowledge` | `bijux-proteomics-knowledge` | `packages/proteomics-knowledge/README.md` | `packages/proteomics-knowledge/tests` | `docs/06-bijux-proteomics-knowledge` |
| `proteomics-lab` | `proteomics-lab` | `proteomics_lab` | `bijux-proteomics-lab` | `packages/proteomics-lab/README.md` | `packages/proteomics-lab/tests` | `docs/07-bijux-proteomics-lab` |

## Reading Order

- choose `bijux-proteomics-dev` for repo policy, docs integrity, release validation, and package boundary checks
- choose `bijux-proteomics-core` for scientific contracts and stable proteomics model behavior
- choose `bijux-proteomics-runtime` only when the concern is orchestration, replay, or execution control
- treat `agentic-proteins` as compatibility stewardship, not a place for new product growth
