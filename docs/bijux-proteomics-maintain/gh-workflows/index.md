---
title: gh-workflows
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# gh-workflows

The workflow section explains the GitHub Actions entrypoints and reusable
building blocks that verify, publish, and document the repository.

Use these pages when you need to know which workflow starts on push, pull
request, tag, or manual dispatch, and how that entrypoint fans out into
repository checks, package matrices, or documentation publication.

The top-level entrypoints are `verify.yml` for pushes and pull requests,
`deploy-docs.yml` for handbook publication from `main`, and `publish.yml` for
release tags. `ci.yml` and `build-release-artifacts.yml` are reusable
workflows called by those entrypoints rather than standalone manual surfaces.

## Pages In This Section

- [verify](verify.md)
- [reusable-workflows](reusable-workflows.md)
- [deploy-docs](deploy-docs.md)
- [publish](publish.md)

## Purpose

Use this section to find the workflow file, trigger, and job tree behind a
repository automation concern.

## Stability

Keep it aligned with the workflow files in `.github/workflows/`.
