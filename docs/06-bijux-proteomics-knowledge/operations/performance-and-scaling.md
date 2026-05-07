---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only when knowledge graph or serialization cost is proven material
- do not weaken reviewability to gain speed
- prefer explicit batching or indexing over hidden semantic shortcuts

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`
- `packages/bijux-proteomics-knowledge/tests`
