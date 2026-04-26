---
title: release-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-19
---

# release-workflows

`release-artifacts.yml` orchestrates tag-driven publication and calls
`release-github.yml`, `release-pypi.yml`, and `release-ghcr.yml` as reusable
workflow surfaces.

The split keeps each publication surface explicit:

- `release-pypi.yml` governs PyPI publication behavior
- `release-ghcr.yml` governs GHCR bundle publication behavior
- `release-github.yml` governs GitHub Release publication behavior
- `release-artifacts.yml` orchestrates build and publish order for tag-driven
  releases

## Workflow Anchors

- `.github/workflows/release-artifacts.yml`
- `.github/workflows/release-github.yml`
- `.github/workflows/release-pypi.yml`
- `.github/workflows/release-ghcr.yml`
- package release metadata and staged release assets

## Current Job Tree

- `release-artifacts.yml`: build matrix and reusable release workflow orchestration
- `release-pypi.yml`: `resolve` and publication jobs for configured package inputs
- `release-ghcr.yml`: `resolve` and per-package GHCR artifact publication
- `release-github.yml`: release planning and GitHub Release publication

## Purpose

This page shows which release surfaces are published and how the tag-driven
workflow split is organized.

## Stability

Keep it aligned with the release workflows and their shared artifact and release
configuration contracts.
