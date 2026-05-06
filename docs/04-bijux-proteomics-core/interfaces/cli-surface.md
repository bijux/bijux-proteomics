---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py` are the command-line surfaces for core contract workflows
- CLI behavior should reveal contract meaning and validation state rather than runtime orchestration detail
- new CLI promises must stay aligned with the stable contract model

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`
