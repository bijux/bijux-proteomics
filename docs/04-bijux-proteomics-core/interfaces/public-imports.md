---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics.program_spec`, `programs`, and `targets` for durable contract imports
- `bijux_proteomics.lifecycle`, `validation`, and `execution_contracts` for readiness and execution rules
- `bijux_proteomics.schema` and `serialization` for portable contract payloads

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli/app.py`
- `packages/bijux-proteomics-core/tests`
