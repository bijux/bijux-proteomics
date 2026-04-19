---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Release and Versioning

The repository uses conventional commit messages and package-local release
metadata so release intent remains understandable years later.

For every publishable package in this repository, version is resolved from Git tags through `hatch-vcs`, with a checked-in fallback version for source trees that are outside a release tag context.

```mermaid
sequenceDiagram
    participant Dev as Maintainer
    participant Git as Git tags
    participant Hatch as hatch-vcs
    participant CI as release-artifacts.yml
    participant Targets as PyPI/GHCR/GitHub Release

    Dev->>Git: create version tag
    Git->>Hatch: resolve package versions
    Git->>CI: trigger release orchestration
    CI->>Targets: build release artifacts
    CI->>Targets: publish through release-pypi.yml, release-ghcr.yml, and release-github.yml
```

## Shared Release Facts

- root commit rules live in `pyproject.toml`
- package versions are resolved per package from the shared `v*` tag line
- `release-artifacts.yml` is tag-triggered and orchestrates package build,
  PyPI publication, GHCR publication, and GitHub release publication workflows
- each publishable package owns its own `CHANGELOG.md`

## Purpose

This page connects repository-wide release conventions to the package release
mechanism.

## Stability

Keep it aligned with the release tooling actually configured in the repository.
