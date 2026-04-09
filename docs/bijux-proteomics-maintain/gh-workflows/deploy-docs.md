---
title: deploy-docs
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# deploy-docs

`deploy-docs.yml` is the workflow that turns the checked-in handbook into the
published site.

Documentation in this repository is treated as a maintained surface, not an
optional by-product. The deploy workflow is therefore part of the
documentation contract rather than a convenience step.

## Workflow Anchors

- `.github/workflows/deploy-docs.yml`
- `mkdocs.yml` and `mkdocs.shared.yml`
- `docs/` as the published source tree

## Purpose

This page records the role of the docs deployment workflow.

## Stability

Keep it aligned with the docs deployment workflow and the published handbook
inputs it relies on.
