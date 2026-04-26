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
`bijux-proteomics`. It preserves legacy runtime imports and entrypoints long
enough for callers to migrate to `bijux-proteomics-runtime`. It is a bridge,
not a center of new development.

## What It Owns

- compatibility forwarding for legacy runtime imports
- preserved legacy CLI and API entrypoints while migration is still justified
- the proof bar for keeping or retiring those preserved surfaces

## What It Refuses

- new canonical runtime behavior
- evidence, scoring, or lab semantics
- repository-health automation

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/)
  when you need the package boundary first.
- Open [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/)
  when the question is a preserved import, CLI, API, or compatibility contract.
- Open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  as soon as the question becomes current execution behavior rather than legacy
  forwarding.

## First Proof Check

- `packages/agentic-proteins`
- `packages/agentic-proteins/src/agentic_proteins`
- `packages/agentic-proteins/tests`

## Boundary

If the behavior would still be desirable after legacy callers disappear, it
probably belongs in the canonical runtime package instead of here.
