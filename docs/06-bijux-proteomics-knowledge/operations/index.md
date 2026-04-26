---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Operations

`bijux-proteomics-knowledge` operations should tell a maintainer how to prove, release, and recover the package without confusing that job with work owned elsewhere.

## Start With

- open [Local Development](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/local-development/) when you are actively changing package behavior
- open [Common Workflows](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/common-workflows/) when you need the normal operating path
- open [Release and Versioning](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/release-and-versioning/) before treating a change as publishable

## Section Pages

- [Installation and Setup](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/common-workflows/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/deployment-boundaries/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/failure-recovery/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/performance-and-scaling/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/security-and-safety/)

## What Operations Means Here

- evidence-state validation, contradiction review, and durable management of knowledge records

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py` and `evidence.py`
- `src/bijux_proteomics_knowledge/confidence/segments.py` and `review.py`
- `packages/bijux-proteomics-knowledge/tests`
