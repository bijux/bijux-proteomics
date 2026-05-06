---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Diagnostics should reveal whether a failure belongs to this package or to a neighbor.

## Operating Rules

- logs and diagnostics should make it obvious when a request passed through the bridge
- observe the runtime handoff, not just local wrapper code
- capture enough evidence to justify retirement decisions later

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `interfaces/http/app.py`
- `src/agentic_proteins/execution/`, `state/`, and `providers/`
- `packages/agentic-proteins/tests`
