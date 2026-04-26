---
title: Quality Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Quality Gates

Repository quality checks belong here so package-level code does not have to
reinvent the same maintenance policy over and over.

The quality surface should stay executable and reviewable. If a quality claim
matters, a maintainer should be able to point to the helper module, the test,
and the workflow step that carry it.

## Current Quality Surfaces

- `quality/deptry_scan.py`
- docs consistency and markdown-link checks in `docs/`
- repository tests under `packages/bijux-proteomics-dev/tests`

## Purpose

This page shows how the maintainer package participates in repository-wide
correctness and consistency.

## Stability

Keep it aligned with the quality checks that actually run in local validation
or CI.
