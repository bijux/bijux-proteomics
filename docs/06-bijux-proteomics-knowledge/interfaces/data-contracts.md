---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts are the quickest way to judge whether a package really owns a concept or is just passing it through.

## Package Surface

- claim and evidence schemas
- confidence, contradiction, and review payloads
- repository-facing records that preserve knowledge state across package boundaries

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/packets.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
