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

- tracked model definitions: 2071
- `basemodel`: 127
- `jsonmodel`: 1586
- `protocol`: 19
- `strenum`: 339

## Package Distribution

- `bijux-proteomics-core`: 915
- `bijux-proteomics-runtime`: 397
- `bijux-proteomics-intelligence`: 261
- `bijux-proteomics-lab`: 236
- `bijux-proteomics-knowledge`: 230
- `bijux-proteomics-foundation`: 32

## Release Rule

- tracked structured model names must be unique across canonical product packages
- duplicate model ownership is release-blocking because it hides SSOT drift behind similar class shapes
- current duplicate model issues: 0

## First Proof Check

- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.csv`
- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.md`
- `packages/bijux-proteomics-dev/tests/quality/architecture/test_duplicate_model_ownership.py`
