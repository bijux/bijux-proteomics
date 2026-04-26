---
title: Root Entrypoints
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Root Entrypoints

Root make entrypoints should be easy to trace.

The top-level command surface starts with `Makefile`, `makes/root.mk`,
`makes/env.mk`, and `makes/packages.mk`. Those files establish repository
environment, package enumeration, and the shared target routing that later
fragments build on.

## Entrypoint Anchors

- `Makefile`
- `makes/root.mk`
- `makes/env.mk`
- `makes/packages.mk`

