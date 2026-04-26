---
title: Workspace Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Workspace Layout

The workspace layout is part of the repository's review model. It separates
product packages, maintainer automation, tracked API artifacts, docs, and root
process surfaces so a reviewer can tell what kind of change is being made
before reading implementation detail.

## Layout Layers

- `packages/` for publishable product packages and the maintainer helper package
- `docs/` for the public handbook split that mirrors the architecture
- `apis/` for tracked API and contract artifacts
- `Makefile`, `makes/`, and `.github/workflows/` for repository-wide process
  and automation surfaces
- `artifacts/` for generated local or CI output that is not governed source

## Why Layout Matters

This structure is not just current arrangement. It protects the distinction
between owned source, tracked contracts, public explanation, and generated run
output. When those categories mix, boundary review gets weaker.

## First Proof Check

- the directory layer where a proposed change lands
- the matching handbook branch that should explain that layer
