---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-intelligence`  
Import root: `bijux_proteomics_intelligence`

Intelligence owns recommendation posture. It may consume replay truth and lab
burden evidence, but it must not pretend to own scientific truth, runtime
transport, or laboratory execution authority.

## Supported Package-Root Imports

- `candidates`
- `governance`
- `interpretation`
- `judgment`
- `learning`
- `posture`
- `reviews`

## Allowed Package Dependencies

- `bijux-proteomics-core`
- `bijux-proteomics-foundation`
- `bijux-proteomics-knowledge`
- `bijux-proteomics-lab`
- `bijux-proteomics-runtime`

These edges are limited to recommendation-facing review work: intelligence may
read evidence owners, runtime replay truth, and lab burden surfaces, but it
must not become the canonical source of those layers.

## Excluded Responsibilities

- canonical scientific entity definitions or parsing
- evidence storage, curation, and truth maintenance
- runtime orchestration, transport, or provider selection
- assay scheduling, execution authority, or operational queue ownership

## Route Elsewhere

- Use `bijux-proteomics-knowledge` when the change alters evidence lineage,
  contradiction handling, or reference-state truth.
- Use `bijux-proteomics-runtime` when the change alters execution control,
  operator entrypoints, or replay behavior.
- Use `bijux-proteomics-lab` when the change alters assay burden, readiness, or
  observed follow-up behavior.
