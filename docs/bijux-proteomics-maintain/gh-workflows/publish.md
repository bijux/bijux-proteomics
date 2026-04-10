---
title: publish
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# publish

`publish.yml` is the workflow that turns reviewed release artifacts into PyPI,
GHCR, and GitHub Release publication events.

It sits on top of the artifact-building workflow and the package matrix. Its
job is not to decide what to release from scratch, but to publish the staged
artifact set defined by the release process and versioning rules already
established in the repository.

## Workflow Anchors

- `.github/workflows/publish.yml`
- `.github/workflows/build-release-artifacts.yml`
- package release metadata and staged release assets

## Current Job Tree

- `build` creates one staged release bundle per publishable package
- `publish_pypi` uploads the Python distributions to PyPI
- `publish_ghcr` publishes the staged release bundle to GHCR as an OCI artifact
- `release` creates the repository GitHub Release and attaches the staged assets

## Purpose

This page explains the repository publication workflow and its dependency on
the reusable artifact-build layer.

## Stability

Keep it aligned with the publication workflow, its matrix, and the staged
artifact inputs it expects.
