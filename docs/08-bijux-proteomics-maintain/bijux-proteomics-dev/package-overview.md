---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-dev` exists so repository-health behavior is reviewable in code instead of being hidden inside workflow YAML and shell fragments.

## What It Owns

- documentation checks and sync helpers under `docs/`
- contract-freeze and API drift helpers under `api/`
- release, security, and quality gates under `release/`, `security/`, and `quality/`
- maintainer tools and trusted-process helpers under `tools/` and `trusted_process.py`

## First Proof Check

- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/`
- `packages/bijux-proteomics-dev/tests`

