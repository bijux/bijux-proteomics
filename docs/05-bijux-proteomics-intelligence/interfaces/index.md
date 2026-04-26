---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Interfaces

`bijux-proteomics-intelligence` interfaces should tell a reader exactly which public surfaces are real, which are only compatibility bridges, and which nearby package actually owns the next step.

## Start With

- open [Public Imports](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/public-imports/) when the question starts from code
- open [Data Contracts](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/data-contracts/) when the question is really about payload meaning or compatibility
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/compatibility-commitments/) before changing any documented public promise

## Section Pages

- [Public Imports](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/public-imports/)
- [Data Contracts](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/artifact-contracts/)
- [API Surface](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/api-surface/)
- [CLI Surface](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/cli-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/configuration-surface/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/operator-workflows/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/interfaces/compatibility-commitments/)

## What This Package Publishes

- decision-layer imports, report artifacts, outcome payloads, and recommendation-facing examples

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates.py`, `policies.py`, and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
