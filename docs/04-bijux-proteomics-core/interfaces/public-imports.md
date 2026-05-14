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

- `bijux_proteomics.domain.program_spec`, `domain.programs`, and `domain.targets` for durable contract imports
- `bijux_proteomics.domain.lifecycle`, `domain.validation`, and `execution.runtime_adapter` for readiness and execution rules
- `bijux_proteomics.io.formats` and `workflow.blueprint` for portable contract payloads and runtime-agnostic workflow plans

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`
