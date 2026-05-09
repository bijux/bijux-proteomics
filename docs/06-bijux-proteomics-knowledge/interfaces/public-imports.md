---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics_knowledge.claims`, `evidence`, and `graph` for canonical knowledge imports
- `bijux_proteomics_knowledge.confidence.segments`, `resolution`, and `review` for trust and adjudication surfaces
- `bijux_proteomics_knowledge.schema`, `serialization`, and `repositories` for durable boundary types

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/decision_briefs.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
