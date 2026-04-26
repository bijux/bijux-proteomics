---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Interfaces

`bijux-proteomics-core` interfaces should tell a reader exactly which public surfaces are real, which are only compatibility bridges, and which nearby package actually owns the next step.

## Start With

- open [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/) when the question starts from code
- open [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/) when the question is really about payload meaning or compatibility
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/) before changing any documented public promise

## Section Pages

- [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/)
- [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/artifact-contracts/)
- [API Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/api-surface/)
- [CLI Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/cli-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/configuration-surface/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/operator-workflows/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/)

## What This Package Publishes

- contract imports, CLI entrypoints, schema outputs, and runtime-facing execution surfaces

## First Proof Check

- `src/bijux_proteomics/program_spec.py`, `programs.py`, and `targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli.py`
- `packages/bijux-proteomics-core/tests`
