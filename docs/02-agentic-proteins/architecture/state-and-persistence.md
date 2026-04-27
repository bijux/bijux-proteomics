---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# State and Persistence

State should become durable in `agentic-proteins` only when this package is the right long-term owner of that meaning. Convenience persistence is one of the fastest ways to create hidden authority.

## Durable Surfaces

- workspace and runtime context in `runtime/`
- legacy state and memory records in `state/` and `memory/`
- report artifacts and replay-related evidence in `report/`

## First Proof Check

- source modules that define the state shape
- serialization or repository tests
- migration or compatibility pages when the state must survive change
