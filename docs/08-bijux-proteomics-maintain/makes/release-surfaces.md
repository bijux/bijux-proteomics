---
title: Release Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Release Surfaces

Release-facing make behavior should be visible before CI calls it.

The repository keeps release-related logic in places such as `makes/publish.mk`,
`makes/bijux-py/repository/publish.mk`, and the build and sbom fragments that
shape artifact creation. Those files are part of the release contract and
should be understandable without opening workflow YAML first. The root publish
makefile now declares the repository-owned version resolver and publication
guard modules that keep tagged releases and staged artifacts aligned.

## Release Anchors

- `makes/publish.mk`
- `makes/bijux-py/repository/publish.mk`
- `makes/bijux-py/ci/build.mk`
- `makes/bijux-py/ci/sbom.mk`

## Purpose

This page records the main make files that influence release preparation and
publication behavior.

## Stability

Keep it aligned with the repository’s actual release-facing make surfaces.
