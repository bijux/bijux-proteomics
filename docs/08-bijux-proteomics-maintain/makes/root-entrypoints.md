---
title: Root Entrypoints
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Root Entrypoints

Root entrypoints are the command names maintainers and CI touch first. They should stay small, obvious, and easy to trace.

## Entry Rules

- keep top-level targets readable from `Makefile`
- route shared behavior into named fragments rather than inline shell complexity
- make the next owning file obvious after one jump

## First Proof Check

- `Makefile`
- `makes/root.mk`

