---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility commitments are expensive promises. They should be visible enough that nobody expands them by accident.

## Package Surface

- planning and outcome payloads should stay stable enough for downstream review
- new lab surface promises should not duplicate shared or intelligence-owned contracts
- persisted lab artifacts require deliberate migration handling when they change

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py`
- `packages/bijux-proteomics-lab/tests`
