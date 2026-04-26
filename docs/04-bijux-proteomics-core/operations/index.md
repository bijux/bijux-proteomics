---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Operations

`bijux-proteomics-core` operations should tell a maintainer how to prove, release, and recover the package without confusing that job with work owned elsewhere.

## Start With

- open [Local Development](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/local-development/) when you are actively changing package behavior
- open [Common Workflows](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/common-workflows/) when you need the normal operating path
- open [Release and Versioning](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/release-and-versioning/) before treating a change as publishable

## Section Pages

- [Installation and Setup](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/common-workflows/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/deployment-boundaries/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/failure-recovery/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/performance-and-scaling/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/security-and-safety/)

## What Operations Means Here

- contract validation, lifecycle review, and stable release of durable core meanings

## First Proof Check

- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
- `packages/bijux-proteomics-core/tests`
