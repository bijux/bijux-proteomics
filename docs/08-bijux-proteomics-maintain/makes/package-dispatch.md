---
title: Package Dispatch
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Package Dispatch

Package dispatch is how shared target families become package-specific without
duplicating the whole command model.

The repository uses `makes/bijux-py/root/package-dispatch.mk` and the files
under `makes/packages/` to route shared target contracts onto real package
roots such as `agentic-proteins`, `bijux-proteomics-core`, and the other
publishable packages.

## Dispatch Anchors

- `makes/bijux-py/root/package-dispatch.mk`
- `makes/packages/agentic-proteins.mk`
- `makes/packages/bijux-proteomics-*.mk`

## Purpose

This page records how package-specific target routing is assembled.

## Stability

Keep it aligned with the package dispatch files that currently exist.
