---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Durable scientific workflow rules belong here before evidence state, ranking
policy, or runtime delivery layers act on them.

## Keep It Here When

- the change alters canonical entities, lifecycle transitions, review gates, or
  runtime-agnostic workflow contracts
- the best proof lives in this package's source tree and tests
- neighboring packages would otherwise become shadow owners of scientific law

## Move It Elsewhere When

- the change mainly alters evidence truth, recommendation posture, runtime
  transport, or assay consequence
- the package becomes a convenience layer for review or operator delivery logic
- the proof surface is mostly outside scientific contracts already

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
