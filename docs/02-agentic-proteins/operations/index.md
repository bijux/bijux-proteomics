---
title: Operations
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Operations

`agentic-proteins` operations should tell a maintainer how to prove, release, and recover the package without confusing that job with work owned elsewhere.

## Start With

- open [Local Development](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/local-development/) when you are actively changing package behavior
- open [Common Workflows](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/common-workflows/) when you need the normal operating path
- open [Release and Versioning](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/release-and-versioning/) before treating a change as publishable

## Section Pages

- [Installation and Setup](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/common-workflows/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/deployment-boundaries/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/failure-recovery/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/performance-and-scaling/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/security-and-safety/)

## What Operations Means Here

- compatibility preservation, migration validation, and safe retirement of legacy runtime behavior

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
