---
title: Operations
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Operations

`bijux-proteomics-intelligence` operations should tell a maintainer how to prove, release, and recover the package without confusing that job with work owned elsewhere.

## Start With

- open [Local Development](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/local-development/) when you are actively changing package behavior
- open [Common Workflows](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/common-workflows/) when you need the normal operating path
- open [Release and Versioning](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/release-and-versioning/) before treating a change as publishable

## Section Pages

- [Installation and Setup](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/common-workflows/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/deployment-boundaries/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/failure-recovery/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/performance-and-scaling/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/security-and-safety/)

## What Operations Means Here

- decision-quality validation, explainability review, and safe evolution of recommendation workflows

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
