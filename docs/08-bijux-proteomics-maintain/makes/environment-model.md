---
title: Environment Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Environment Model

Environment handling should make local and CI execution reproducible without hiding required assumptions.

## Environment Rules

- centralize shared environment logic in dedicated fragments
- keep package-specific overrides visible
- fail early when required tooling assumptions are missing

## First Proof Check

- `makes/env.mk`
- env-related includes under `makes/bijux-py/`

