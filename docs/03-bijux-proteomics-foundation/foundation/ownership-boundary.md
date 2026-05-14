---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

Shared primitives belong here before downstream packages attach lifecycle law,
evidence judgment, recommendation posture, or runtime execution.

## Keep It Here When

- the change defines an identifier, schema profile, canonical JSON shape, or
  deterministic hash rule
- the best proof lives in this package's source tree and tests
- neighboring packages would otherwise fork primitive meaning or migration law

## Move It Elsewhere When

- the change mainly alters lifecycle semantics, benchmark truth, evidence
  posture, recommendation policy, or runtime behavior
- the package becomes a convenience layer for higher-level product logic
- the proof surface is mostly outside shared primitives already

## First Proof Check

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- `packages/bijux-proteomics-foundation/tests`
