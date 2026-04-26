---
title: reusable-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-19
---

# reusable-workflows

The repository uses reusable workflow files to keep package verification and
release publication contracts consistent across packages.

`ci.yml` defines the reusable package-check wrapper and delegates execution to
`bijux-std` reusable CI contracts. `release-artifacts.yml` can run as a
standalone tag-triggered workflow and as a reusable orchestration workflow for
build and publication stages.

## Workflow Anchors

- `.github/workflows/ci.yml`
- `.github/workflows/release-artifacts.yml`
- the package matrix caller in `verify.yml`
- release callers in `release-pypi.yml`, `release-ghcr.yml`, and
  `release-github.yml`

