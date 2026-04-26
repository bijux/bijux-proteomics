---
title: Release Support
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Release Support

Release support should make version and publication rules visible before tags and workflows do the irreversible part.

## Support Rules

- keep version resolution and changelog checks explicit
- block publication when repository proof is incomplete
- tie release decisions back to checked-in policy helpers

## First Proof Check

- `src/bijux_proteomics_dev/release/version_resolver.py`
- `src/bijux_proteomics_dev/release/changelog_version.py`
- `src/bijux_proteomics_dev/release/publication_guard.py`

