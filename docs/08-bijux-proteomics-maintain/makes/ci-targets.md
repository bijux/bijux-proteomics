---
title: CI Targets
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# CI Targets

The CI make surface should be explicit enough that workflow files are not the
only place where verification logic can be understood.

`makes/bijux-py/ci/` defines the main CI-oriented target families for build,
docs, lint, quality, sbom, security, test, and shared utility behavior. Those
fragments are the reusable command layer that the workflows depend on.

## CI Anchors

- `makes/bijux-py/ci/build.mk`
- `makes/bijux-py/ci/docs.mk`
- `makes/bijux-py/ci/lint.mk`
- `makes/bijux-py/ci/quality.mk`
- `makes/bijux-py/ci/security.mk`
- `makes/bijux-py/ci/test.mk`

