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

Version resolution currently follows two patterns in this repository: Hatch VCS
for `agentic-proteins` and `bijux-proteomics-dev`, and explicit versions for
the remaining publishable packages.

## Shared Release Facts

- root commit rules live in `pyproject.toml`
- package versions are resolved per package
- `publish.yml` is tag-triggered and publishes one matrix entry per package
- each publishable package owns its own `CHANGELOG.md`

## Purpose

This page connects repository-wide release conventions to the package release
mechanism.

## Stability

Keep it aligned with the release tooling actually configured in the repository.
