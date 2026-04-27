---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# State and Persistence

State should become durable in `bijux-proteomics-knowledge` only when this package is the right long-term owner of that meaning. Convenience persistence is one of the fastest ways to create hidden authority.

## Durable Surfaces

- claim and evidence records
- confidence segments and contradiction-resolution state
- review outputs and durable serialized knowledge payloads

## First Proof Check

- source modules that define the state shape
- serialization or repository tests
- migration or compatibility pages when the state must survive change
