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

- tracked model definitions: 1602
- `basemodel`: 127
- `jsonmodel`: 1212
- `protocol`: 19
- `strenum`: 244

## Package Distribution

- `bijux-proteomics-core`: 934
- `bijux-proteomics-lab`: 192
- `bijux-proteomics-runtime`: 167
- `bijux-proteomics-intelligence`: 158
- `bijux-proteomics-knowledge`: 125
- `bijux-proteomics-foundation`: 26

## Release Rule

- tracked structured model names must be unique across canonical product packages
- duplicate model ownership is release-blocking because it hides SSOT drift behind similar class shapes
- current duplicate model issues: 0

## First Proof Check

- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.csv`
- `docs/01-bijux-proteomics/foundation/duplicate-model-ownership.md`
- `packages/bijux-proteomics-dev/tests/test_duplicate_model_ownership.py`
