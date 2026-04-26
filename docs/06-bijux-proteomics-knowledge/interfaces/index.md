---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Interfaces

`bijux-proteomics-knowledge` interfaces should tell a reader exactly which public surfaces are real, which are only compatibility bridges, and which nearby package actually owns the next step.

## Start With

- open [Public Imports](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/public-imports/) when the question starts from code
- open [Data Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/data-contracts/) when the question is really about payload meaning or compatibility
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/compatibility-commitments/) before changing any documented public promise

## Section Pages

- [Public Imports](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/public-imports/)
- [Data Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/artifact-contracts/)
- [API Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/api-surface/)
- [CLI Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/cli-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/configuration-surface/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/operator-workflows/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/compatibility-commitments/)

## What This Package Publishes

- canonical evidence imports, review payloads, repository-facing schemas, and contradiction-aware artifacts

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py`, `evidence.py`, and `graph.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py`, `resolution.py`, and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
