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

- tracked model definitions: 1633
- `basemodel`: 127
- `jsonmodel`: 1230
- `protocol`: 19
- `strenum`: 257

## Package Distribution

- `bijux-proteomics-core`: 730
- `bijux-proteomics-runtime`: 340
- `bijux-proteomics-lab`: 207
- `bijux-proteomics-intelligence`: 199
- `bijux-proteomics-knowledge`: 126
- `bijux-proteomics-foundation`: 31

## Release Rule

- tracked structured model names must be unique across canonical product packages
- duplicate model ownership is release-blocking because it hides SSOT drift behind similar class shapes
- current duplicate model issues: 0

## First Proof Check

- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.csv`
- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.md`
- `packages/bijux-proteomics-dev/tests/quality/architecture/test_duplicate_model_ownership.py`
