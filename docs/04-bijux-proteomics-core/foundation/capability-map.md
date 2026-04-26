---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Capability Map

The capability map lists the kinds of work `bijux-proteomics-core` is allowed to do.
That list should make the package easier to defend in review, not broader by
default.

## Allowed Capability Classes

- define program specifications and lifecycle state
- encode gates and operating constraints
- publish stable core contracts to downstream packages

## Disallowed Expansion

- shared schema primitives
- evidence truth
- operator-facing runtime execution

## First Proof Check

- [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- the package source and tests that prove the claimed capability
