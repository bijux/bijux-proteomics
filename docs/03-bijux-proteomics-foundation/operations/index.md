---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Operations

`bijux-proteomics-foundation` operations should tell a maintainer how to prove, release, and recover the package without confusing that job with work owned elsewhere.

## Start With

- open [Local Development](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/local-development/) when you are actively changing package behavior
- open [Common Workflows](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/common-workflows/) when you need the normal operating path
- open [Release and Versioning](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/release-and-versioning/) before treating a change as publishable

## Section Pages

- [Installation and Setup](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/common-workflows/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/deployment-boundaries/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/failure-recovery/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/performance-and-scaling/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/security-and-safety/)

## What Operations Means Here

- shared-schema validation, migration safety, and cross-package compatibility proof

## First Proof Check

- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
- `packages/bijux-proteomics-foundation/tests`
