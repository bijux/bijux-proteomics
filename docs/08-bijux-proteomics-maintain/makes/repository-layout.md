---
title: Repository Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Repository Layout

The layout of `makes/` is part of the repository architecture.

Repository-wide fragments live near the root, reusable `bijux-py` logic lives
under `makes/bijux-py/`, and package-facing bindings live under
`makes/packages/`. That split keeps shared logic reusable without blurring it
into per-package bindings.

## Layout Anchors

- `makes/root.mk`, `makes/env.mk`, and `makes/packages.mk`
- `makes/bijux-py/root/`
- `makes/bijux-py/repository/`
- `makes/bijux-py/ci/`
- `makes/packages/`

