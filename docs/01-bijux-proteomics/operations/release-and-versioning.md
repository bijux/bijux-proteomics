---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

Release discipline matters most where several publishable packages move
together. In this repository, versioning should make compatibility-sensitive
change visible rather than hide it behind generic release automation.

## Shared Release Facts

- root commit rules live in `pyproject.toml`
- package versions resolve from shared `v*` tags through `hatch-vcs`
- release workflows coordinate build, PyPI publication, GHCR publication, and
  GitHub release output
- each publishable package owns its own `CHANGELOG.md`

## Compatibility Triggers

Treat a release as repository-significant when it changes tracked API
artifacts, runtime migration posture, package routing, or another surface that
several packages or external consumers depend on together.

## First Proof Check

- package metadata and changelogs
- release workflows under `.github/workflows/`
- publication guard and version resolver helpers in `bijux-proteomics-dev`
