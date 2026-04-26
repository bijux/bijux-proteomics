---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Interfaces

`bijux-proteomics-foundation` interfaces should tell a reader exactly which public surfaces are real, which are only compatibility bridges, and which nearby package actually owns the next step.

## Start With

- open [Public Imports](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/public-imports/) when the question starts from code
- open [Data Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/data-contracts/) when the question is really about payload meaning or compatibility
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/compatibility-commitments/) before changing any documented public promise

## Section Pages

- [Public Imports](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/public-imports/)
- [Data Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/artifact-contracts/)
- [API Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/api-surface/)
- [CLI Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/cli-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/configuration-surface/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/operator-workflows/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/compatibility-commitments/)

## What This Package Publishes

- shared Python imports, schema types, serialization helpers, and migration contracts

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py`
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
