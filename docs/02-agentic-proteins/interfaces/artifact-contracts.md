---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Artifacts matter because they survive the moment of execution and become someone else's input or evidence.

The canonical runtime API root is `apis/bijux-proteomics-runtime/v1`; the compatibility mirror root is `apis/agentic-proteins/v1`.

## Package Surface

- structure-report outputs produced through `interfaces/structure_reports.py`
- runtime and workspace state carried through `execution/` and `state/`
- legacy execution or replay artifacts still needed for migration review

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py`
- `src/agentic_proteins/interfaces/http/app.py`
- `packages/agentic-proteins/tests`
