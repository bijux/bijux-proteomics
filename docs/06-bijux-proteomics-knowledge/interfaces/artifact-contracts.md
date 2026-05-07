---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Artifacts matter because they survive the moment of execution and become someone else's input or evidence.

## Package Surface

- claim, evidence, and graph payloads
- confidence segments and review outputs
- serialized knowledge records used by other packages

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/packets.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
