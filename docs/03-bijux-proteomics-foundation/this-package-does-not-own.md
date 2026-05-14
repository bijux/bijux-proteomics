---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-foundation`  
Import root: `bijux_proteomics_foundation`

Foundation is the shared primitive layer. It should stop at identifiers,
serialization, stable document shape, and migration-safe utility behavior.

## Supported Package-Root Imports

- `DocumentSchema`
- `JsonModel`
- `hash_payload`
- `to_canonical_json`

## Allowed Package Dependencies

This package should remain package-self-contained. It may not depend on another
publishable product package to define its own meaning.

## Excluded Responsibilities

- program lifecycle and gate logic
- candidate ranking and decision policies
- evidence conflict semantics or lab planning behavior

## Route Elsewhere

- Use `bijux-proteomics-core` when the question becomes lifecycle truth,
  workflow rules, or benchmark-acceptance logic.
- Use `bijux-proteomics-knowledge` when the question becomes evidence memory,
  contradiction handling, or reference-grounded scientific review.
- Use `bijux-proteomics-runtime` when the question becomes execution
  coordination, replay, or operator entrypoints.
