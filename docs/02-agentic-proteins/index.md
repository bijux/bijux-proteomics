---
title: agentic-proteins
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# agentic-proteins

`agentic-proteins` is the strict compatibility package in
`bijux-proteomics`. Its job is to preserve legacy import paths and CLI
entrypoints long enough for callers to move safely to
`bijux-proteomics-runtime`.

Treat this package as a bridge, not as the center of new development. It keeps
the preserved surface, the canonical owner, and the retirement bar explicit.

Legacy callers often arrive here first because they still remember the
old package name. This page routes them quickly from that old
entrypoint to the current owner without hiding the remaining
compatibility burden.

## Start Here

- open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  when the question is about current execution behavior, providers, API, or
  CLI ownership
- open [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/) when the real
  question is migration policy, release policy, or repository-wide governance
- stay here only while the question is about preserved legacy names and the
  proof bar for keeping them

## What This Package Owns

- preserved legacy import names that forward to canonical package surfaces
- compatibility review for whether each preserved name still earns its place
- migration guidance that tells readers where the canonical owner now lives

## What This Package Does Not Own

- new runtime behavior, orchestration, or operator-facing execution logic
- canonical confidence semantics now owned by
  `bijux-proteomics-knowledge`
- canonical reporting semantics now owned by
  `bijux-proteomics-intelligence`

## Open This Section When

- you need compatibility-safe legacy import or CLI entrypoints
- you are validating forwarding boundaries and migration promises
- you need to trace older runtime usage to the canonical runtime package

## Open The Canonical Handbook When

- you are designing a new caller and can depend on the canonical package now
- you need current runtime operation or API behavior rather than legacy naming
- you are looking for biological, evidence, or scoring semantics directly

## Package Sections

- [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/)
- [Quality](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/)

## Cross-Package Handoffs

- open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) when the question is about current runtime behavior
- open [Repository Handbook](https://bijux.io/bijux-proteomics/01-bijux-proteomics/) when the question is about migration policy or repository-wide release rules
- stay here only while the question is about preserved legacy surfaces and their retirement bar

## Concrete Anchors

- `packages/agentic-proteins` for the compatibility package root
- `packages/agentic-proteins/src/agentic_proteins/__init__.py` for the actual
  forwarding surface that remains preserved
- `packages/agentic-proteins/tests` for forwarding and compatibility proof

## Bottom Line

`agentic-proteins` stays narrow, explicit, and temporary. If a legacy name
still exists, this handbook must keep the forwarding target and the retirement
decision clear enough that readers are not trapped in the bridge.
