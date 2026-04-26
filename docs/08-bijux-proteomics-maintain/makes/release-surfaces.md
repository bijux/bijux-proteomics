---
title: Release Surfaces
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Release Surfaces

Release surfaces are where local commands and publication workflows meet. They deserve explicit routing and explicit failure points.

## Release Rules

- keep publication targets easy to trace from the root surface
- align make release targets with workflow release stages
- treat release shortcuts that skip proof as defects

## First Proof Check

- `makes/publish.mk`
- release workflow files under `.github/workflows/`

