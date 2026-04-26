---
title: Schema Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Schema Governance

Schema drift is one of the fastest ways to let a package family tell two
different stories at once. The maintainer package exists in part to stop that
drift from becoming a hidden cost.

Repository-level schema helpers make contract changes visible before
release, not after downstream users discover disagreement between code and
checked-in API artifacts.

## Current Schema Surfaces

- `api/freeze_contracts.py`
- `api/openapi_drift.py`
- `apis/*/v1/` as the checked reference contracts they enforce

## Purpose

This page shows why schema drift detection belongs in the maintainer package
instead of scattered shell scripts.

## Stability

Keep it aligned with the actual API tooling and tracked schema files.
