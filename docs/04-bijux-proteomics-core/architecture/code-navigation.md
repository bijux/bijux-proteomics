---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-core` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py` for contract roots
- `src/bijux_proteomics/domain/lifecycle.py`, `domain/validation.py`, and `execution/backend.py` for readiness and flow
- `packages/bijux-proteomics-core/tests` for contract-proof coverage

## First Proof Check

- the source tree in `packages/bijux-proteomics-core/src/bijux_proteomics`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
