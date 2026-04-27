---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Capability Map

The capability map lists the kinds of work `bijux-proteomics-foundation` is allowed to do.
That list should make the package easier to defend in review, not broader by
default.

## Allowed Capability Classes

- define shared identifiers
- govern schema and serialization compatibility
- carry migration helpers for payload evolution

## Disallowed Expansion

- program policy
- evidence truth and contradictions
- execution orchestration

## First Proof Check

- [Package Overview](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/package-overview/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/ownership-boundary/)
- the package source and tests that prove the claimed capability
