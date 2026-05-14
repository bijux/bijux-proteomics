---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

The release version is explicit in Git history because version is resolved from Git tags through `hatch-vcs`.

Release rules should explain what kind of change readers need to look for before they trust a version bump.

## Operating Rules

- release notes should state whether contract meaning changed, narrowed, or stayed stable
- release notes that mention quantification must say whether the change improves `[accuracy]`, `[robustness]`, `[interpretability]`, or only `[implementation]`
- downstream package owners deserve visible notice when lifecycle or schema rules move
- avoid bundling unrelated contract and operational changes together
- release-facing scope claims must stay aligned with the repository-wide
  [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`
