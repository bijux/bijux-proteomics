---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-knowledge` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py` for canonical structures
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/packets.py`, and `reviews/provenance.py` for trust and contradiction handling
- `packages/bijux-proteomics-knowledge/tests` for proof of evidence semantics

## First Proof Check

- the source tree in `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
