---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-proteomics-knowledge` stays reviewable only when its structural families remain easy to name and defend. The package owns evidence, claims, confidence, and contradiction handling, so its modules should read like one coherent argument for that role.

## Owned Module Families

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py` own canonical knowledge structures
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/packets.py`, and `reviews/provenance.py` own trust, contradiction, and adjudication logic
- `src/bijux_proteomics_knowledge/contracts/schema.py`, `references/public.py`, and `reviews/trends.py` own durable boundaries for knowledge state

## First Proof Check

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- the matching package tests
- neighboring handbook branches when a module starts to look shared
