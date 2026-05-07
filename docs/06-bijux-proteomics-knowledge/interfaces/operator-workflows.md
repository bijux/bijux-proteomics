---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Operator workflows should say who uses the surface, why they use it, and when they should stop and open a neighbor handbook instead.

## Package Surface

- developers modeling new evidence shapes
- reviewers checking contradiction and confidence behavior
- downstream packages consuming reviewed knowledge outputs

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py`, `memory/models/evidence.py`, and `memory/integrity/graph.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py`, `reviews/packets.py`, and `reviews/provenance.py`
- `packages/bijux-proteomics-knowledge/tests`
