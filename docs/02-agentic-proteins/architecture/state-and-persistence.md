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

- workspace and run context in `state/`
- legacy run outputs, snapshots, and request records in `state/`
- execution artifacts that still matter only because migration remains open

## First Proof Check

- source modules that define the state shape
- serialization or repository tests
- migration or compatibility pages when the state must survive change
