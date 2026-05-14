---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Operator workflows should say who uses the surface, why they use it, and when they should stop and open a neighbor handbook instead.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- operators preserving an existing entrypoint while moving toward runtime
- maintainers verifying that a legacy surface still forwards correctly
- reviewers deciding whether a compatibility promise can finally be removed

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/interfaces/http/app.py`
- `packages/agentic-proteins/tests`
