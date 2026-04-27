---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release notes should explain decision-surface changes in reader language
- artifact shape changes need downstream warning and proof
- avoid combining policy shifts with unrelated structural cleanup in one release story

## First Proof Check

- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
