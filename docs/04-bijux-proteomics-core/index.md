---
title: bijux-proteomics-core
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-core

`bijux-proteomics-core` owns durable program contracts in
`bijux-proteomics`. It is where workflows, lifecycle state, gates, and other
long-lived rules are defined before downstream packages score, execute, or act
on them.

## What It Owns

- program models and lifecycle rules
- gate semantics and durable workflow constraints
- core contracts that downstream packages depend on

## What It Refuses

- shared serialization primitives that belong in foundation
- evidence truth and confidence policy that belong in knowledge
- execution orchestration that belongs in runtime

## Start With

- Open [Foundation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/)
  for the package role and contract boundary.
- Open [Interfaces](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/)
  when the issue is a public contract or package-facing surface.
- Open [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
  when the concern becomes recommendation policy rather than durable program
  rules.

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- public contract artifacts when a core API surface changes
