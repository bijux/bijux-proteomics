---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release notes should call out planning or outcome contract changes clearly
- persisted lab artifact changes need migration thinking
- avoid mixing operator-facing payload shifts with unrelated cleanup

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/repositories.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
