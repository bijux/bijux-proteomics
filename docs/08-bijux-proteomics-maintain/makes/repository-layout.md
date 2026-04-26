---
title: Repository Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Repository Layout

Make routing reflects repository layout. If the layout and the targets drift apart, maintainer work becomes guesswork.

## Layout Rules

- shared repository targets stay in shared fragments
- package-specific rules stay under `makes/packages/`
- keep naming aligned with real repository and package boundaries

## First Proof Check

- `makes/`
- `makes/packages/`

