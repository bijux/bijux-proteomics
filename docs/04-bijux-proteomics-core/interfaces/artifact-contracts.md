---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Artifacts matter because they survive the moment of execution and become someone else's input or evidence.

## Package Surface

- serialized contract payloads
- program, target, and readiness records
- execution-contract artifacts consumed by runtime or downstream packages

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli/app.py`
- `packages/bijux-proteomics-core/tests`
