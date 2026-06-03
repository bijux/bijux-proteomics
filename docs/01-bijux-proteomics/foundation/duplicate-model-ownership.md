---
title: Duplicate Model Ownership
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-dev
last_reviewed: 2026-05-05
---

# duplicate model ownership

This report tracks structured model names across the six real product packages. A tracked model name must belong to exactly one canonical package.

## Current Counts

- tracked model definitions: 3956
- `basemodel`: 127
- `jsonmodel`: 3116
- `protocol`: 20
- `strenum`: 693

## Package Distribution

- `bijux-proteomics-core`: 2643
- `bijux-proteomics-runtime`: 474
- `bijux-proteomics-intelligence`: 293
- `bijux-proteomics-knowledge`: 268
- `bijux-proteomics-lab`: 244
- `bijux-proteomics-foundation`: 34

## Release Rule

- tracked structured model names must be unique across canonical product packages
- duplicate model ownership is release-blocking because it hides SSOT drift behind similar class shapes
- current duplicate model issues: 0

## First Proof Check

- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.csv`
- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.md`
- `packages/bijux-proteomics-dev/tests/quality/architecture/test_duplicate_model_ownership.py`
