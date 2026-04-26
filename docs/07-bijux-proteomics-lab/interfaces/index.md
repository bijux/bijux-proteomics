---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Interfaces

`bijux-proteomics-lab` interfaces should tell a reader exactly which public surfaces are real, which are only compatibility bridges, and which nearby package actually owns the next step.

## Start With

- open [Public Imports](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/public-imports/) when the question starts from code
- open [Data Contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/data-contracts/) when the question is really about payload meaning or compatibility
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/compatibility-commitments/) before changing any documented public promise

## Section Pages

- [Public Imports](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/public-imports/)
- [Data Contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/artifact-contracts/)
- [API Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/api-surface/)
- [CLI Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/cli-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/configuration-surface/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/operator-workflows/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/compatibility-commitments/)

## What This Package Publishes

- planning and outcome imports, lab payloads, repository contracts, and operator-facing examples

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/schema.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
