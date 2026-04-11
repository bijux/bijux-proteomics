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

Every publishable package in this repository resolves version from Git tags
through `hatch-vcs`, with a checked-in fallback version for source trees that
are outside a release tag context.

## Shared Release Facts

- root commit rules live in `pyproject.toml`
- package versions are resolved per package from the shared `v*` tag line
- `publish.yml` is tag-triggered and fans out into build, PyPI, GHCR, and GitHub Release jobs
- each publishable package owns its own `CHANGELOG.md`

## Purpose

This page connects repository-wide release conventions to the package release
mechanism.

## Stability

Keep it aligned with the release tooling actually configured in the repository.
