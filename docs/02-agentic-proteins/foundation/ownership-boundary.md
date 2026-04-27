---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Compatibility forwarding belongs here only while legacy callers still need it. Canonical runtime behavior belongs in `bijux-proteomics-runtime`.

## Keep It Here When

- the change strengthens the package's named role
- the best proof lives in this package's source tree and tests
- neighboring packages would become less honest if they absorbed the behavior

## Move It Elsewhere When

- the change mainly alters a neighbor's public contract
- the package becomes a convenience layer instead of an accountable owner
- the proof surface is mostly outside this package already

## First Proof Check

- `packages/agentic-proteins/src/agentic_proteins`
- `packages/agentic-proteins/tests`
