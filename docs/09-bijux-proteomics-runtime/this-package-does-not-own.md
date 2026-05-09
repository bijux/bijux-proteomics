---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-runtime`  
Import root: `bijux_proteomics_runtime`

Runtime owns execution control and replay-safe operator surfaces. It may stitch
cross-package evidence together for rerun review, but it must not invent the
scientific, recommendation, or lab meaning carried through that chain.

## Supported Package-Root Imports

- `AppConfig`
- `create_app`
- `RunManager`
- `cli`

## Allowed Package Dependencies

- `bijux-proteomics-core`
- `bijux-proteomics-foundation`
- `bijux-proteomics-intelligence`
- `bijux-proteomics-knowledge`
- `bijux-proteomics-lab`

These edges are governed because runtime assembles replayable workflow evidence
from upstream and downstream owners, but runtime remains responsible only for
execution control, artifacts, and operator entrypoints.

## Excluded Responsibilities

- canonical domain definitions
- evidence semantics and contradiction semantics
- scoring policy semantics and recommendation semantics
- lab planning semantics and experiment promotion semantics

## Route Elsewhere

- Use `bijux-proteomics-core` when the change alters workflow contracts or
  runtime-agnostic scientific rules.
- Use `bijux-proteomics-knowledge` when the change alters evidence truth,
  contradiction handling, or curated reference support.
- Use `bijux-proteomics-lab` when the change alters assay planning, readiness,
  or observed outcome promotion.
