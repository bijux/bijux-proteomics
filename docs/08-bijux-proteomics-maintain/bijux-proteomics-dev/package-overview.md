---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Package Overview

`bijux-proteomics-dev` exists to keep repository-wide rules in one code-bearing
home. It owns the automation that checks schema drift, docs integrity,
dependency policy, release metadata, and maintainer utility flows.

The package is intentionally separate from the publishable product surfaces.
That separation makes it easier to review repository-health changes without
pretending they are part of runtime or scientific domain behavior.

## What It Owns

- shared docs validation and architecture consistency helpers
- API freeze and OpenAPI drift enforcement
- release metadata and changelog checks
- dependency allowlist and vulnerability gates
- maintainer utility commands that support repeatable repository workflows

## Purpose

This page gives the shortest honest description of why the maintainer package
exists.

## Stability

Keep it aligned with the real repository-health code under
`packages/bijux-proteomics-dev/src/bijux_proteomics_dev/`.
