---
title: reusable-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# reusable-workflows

The repository uses reusable workflows to keep package verification and release
artifact creation consistent across packages.

`ci-package.yml` defines the reusable package-check contract, while
`build-release-artifacts.yml` defines the reusable artifact-build contract used
by publication flow. Grouping them together makes their role clear: they are
workflow building blocks rather than top-level entrypoints.

## Workflow Anchors

- `.github/workflows/ci-package.yml`
- `.github/workflows/build-release-artifacts.yml`
- the package-matrix callers in `verify.yml` and `publish.yml`

## Purpose

This page explains the reusable workflow contracts that other workflows depend
on.

## Stability

Keep it aligned with the reusable workflow files and their current callers.
