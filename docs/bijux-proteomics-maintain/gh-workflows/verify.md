---
title: verify
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-19
---

# verify

`verify.yml` is the main repository verification workflow.

It is the workflow that decides whether repository automation contracts and the
package matrix are healthy enough to trust on pushes and pull requests. That
makes it the broadest CI truth for day-to-day repository changes.

The job tree is intentionally split. `repository` runs shared automation
contracts first, `package` fans out by package through `ci.yml`, and each
package run uses the shared `bijux-std` reusable CI workflow.

## Workflow Anchors

- `.github/workflows/verify.yml`
- repository checks driven from `make`
- the package matrix that delegates to reusable package workflows

## Purpose

Use this page to understand when verification runs and how it branches from
repository checks into package-level jobs.

## Stability

Keep it aligned with the real trigger paths, repository job, and package matrix
declared in `verify.yml`.
