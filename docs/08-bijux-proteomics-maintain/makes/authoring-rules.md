---
title: Authoring Rules
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Authoring Rules

Make authoring rules should keep the command surface auditable as it grows.

## Rules

- prefer named fragments over dense inline shell logic
- keep target names and file names aligned with the owning concept
- refactor when shared targets start hiding package-specific behavior

## First Proof Check

- `Makefile`
- `makes/root.mk` and related fragments

