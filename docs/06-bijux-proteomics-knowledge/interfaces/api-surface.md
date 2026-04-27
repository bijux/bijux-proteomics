---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# API Surface

An API surface is only real when the package actually owns the network-facing contract, not when docs are trying to look complete.

## Package Surface

- this package does not own a standalone HTTP API product surface
- knowledge data may travel through service layers elsewhere, but the public contract here is the evidence model itself
- if a service need appears local, confirm that the interface is not really a shared schema concern

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py`, `evidence.py`, and `graph.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py`, `resolution.py`, and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
