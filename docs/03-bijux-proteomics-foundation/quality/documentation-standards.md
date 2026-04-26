---
title: Documentation Standards
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Documentation Standards

Documentation standards should protect the reader from filler, drift, and false confidence.

## Review Rules

- docs should describe shared meaning before implementation detail
- examples should show how types travel across packages
- compatibility notes should read like release-critical guidance

## First Proof Check

- `packages/bijux-proteomics-foundation/tests`
- `src/bijux_proteomics_foundation/schema.py` and `migrations.py`
- `src/bijux_proteomics_foundation/serialization.py`
