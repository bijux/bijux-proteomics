---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Execution Model

The execution model for `agentic-proteins` should make it clear how package-owned work progresses without quietly taking over a neighbor's job.

## Flow

- legacy CLI, API, or import entrypoints arrive through `interfaces/` or `api/`
- compatibility logic in `core/` and `execution/` translates the request into runtime-compatible behavior
- runtime, provider, report, and state modules preserve inspectable outputs until the path can be retired

## First Proof Check

- the owning modules for each flow stage
- package tests that prove the transition points
- downstream or upstream handbooks when the flow crosses package boundaries
