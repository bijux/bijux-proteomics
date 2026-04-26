---
title: Release Support
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Release Support

Shared release checks belong here so package metadata, changelog expectations,
and publication readiness stay consistent across the repository.

The point is not to hide release logic behind a helper package. The point is to
make release support visible in one place where maintainers can audit the rules
that repository automation is actually enforcing.

## Current Release Surfaces

- `release/changelog_version.py`
- `release/version_resolver.py`
- `release/publication_guard.py`
- package metadata checks in repository tests
- root commit conventions configured through commitizen

