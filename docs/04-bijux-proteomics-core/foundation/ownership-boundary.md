---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Durable workflow rules belong here before evidence state, scoring policy, or execution layers act on them.

## Keep It Here When

- the change strengthens the package's named role
- the best proof lives in this package's source tree and tests
- neighboring packages would become less honest if they absorbed the behavior

## Move It Elsewhere When

- the change mainly alters a neighbor's public contract
- the package becomes a convenience layer instead of an accountable owner
- the proof surface is mostly outside this package already

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
