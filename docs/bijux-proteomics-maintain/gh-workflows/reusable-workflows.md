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

`ci.yml` defines the reusable package-check contract, while
`build-release-artifacts.yml` defines the reusable artifact-build contract used
by publication flow. Grouping them together makes their role clear: they are
workflow building blocks rather than top-level entrypoints, so they run through
their callers instead of appearing as separate manual workflows. Their job names
stay package-scoped so the Actions UI shows which package and check actually
ran.

## Workflow Anchors

- `.github/workflows/ci.yml`
- `.github/workflows/build-release-artifacts.yml`
- the package-matrix callers in `verify.yml` and `publish.yml`

## Purpose

Use this page to see which workflows are building blocks and which top-level
workflows call them.

## Stability

Keep it aligned with the reusable workflow files and their current callers.
