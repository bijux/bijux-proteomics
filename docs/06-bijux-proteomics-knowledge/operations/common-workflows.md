---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- review a knowledge change against claim, evidence, confidence, and review outputs
- check whether downstream consumers still interpret the record the same way
- update examples when canonical knowledge artifacts change meaning

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`
- `packages/bijux-proteomics-knowledge/tests`
