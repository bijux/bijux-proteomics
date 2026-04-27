---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# State and Persistence

State should become durable in `bijux-proteomics-intelligence` only when this package is the right long-term owner of that meaning. Convenience persistence is one of the fastest ways to create hidden authority.

## Durable Surfaces

- candidate sets and ranking factors
- evaluation outputs and decision outcomes
- briefing and report artifacts that justify recommendations

## First Proof Check

- source modules that define the state shape
- serialization or repository tests
- migration or compatibility pages when the state must survive change
