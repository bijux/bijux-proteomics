---
title: Package Dispatch
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Package Dispatch

Package dispatch should explain how one target reaches one package or many without hiding the routing logic.

## Dispatch Rules

- dispatch through named package fragments
- keep per-package routing explicit in `makes/packages/*.mk`
- avoid shared targets that secretly special-case one package too much

## First Proof Check

- `makes/packages.mk`
- `makes/packages/*.mk`

