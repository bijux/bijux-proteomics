---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Capability Map

The capability map lists the kinds of work `agentic-proteins` is allowed to do.
That list should make the package easier to defend in review, not broader by
default.

## Allowed Capability Classes

- preserve legacy import paths
- preserve legacy CLI and API entry surfaces
- route readers and callers to the canonical runtime package

## Disallowed Expansion

- new canonical runtime behavior
- new evidence or scoring semantics
- maintainer-only repository automation

## First Proof Check

- [Package Overview](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/package-overview/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/ownership-boundary/)
- the package source and tests that prove the claimed capability
