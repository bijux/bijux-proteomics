---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

Deployment boundaries matter because a package can be publishable without being the right place to run a service.

## Operating Rules

- this package is published as shared code, not deployed as an operator-facing service
- deployment boundaries are release and dependency boundaries rather than runtime infrastructure
- if a deployment story seems necessary here, the real question is probably about a consuming package

## First Proof Check

- `src/bijux_proteomics_foundation/documents.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests`
