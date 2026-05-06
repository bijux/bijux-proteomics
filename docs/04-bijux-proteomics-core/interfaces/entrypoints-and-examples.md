---
title: Entrypoints and Examples
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Entrypoints and Examples

Examples should route readers into the real surface quickly and avoid making side paths look canonical.

## Package Surface

- show imports and CLI usage that clarify the contract layer
- prefer examples that separate core meaning from runtime execution
- use schema examples when compatibility is the real concern

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`
