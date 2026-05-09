---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration belongs in the public surface only when a reader must understand it to use the package safely.

## Package Surface

- confidence and review-model choices that remain visible in outputs
- serialization and repository expectations for durable evidence state
- compatibility settings only where knowledge meaning must remain stable across versions

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/decision_briefs.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
