---
title: Make System Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Make System Overview

The make system is a real interface, not a random collection of shortcuts.

## Overview

- `Makefile` is the top entry surface
- shared routing lives in `makes/root.mk`, `makes/packages.mk`, `makes/publish.mk`, and `makes/env.mk`
- package and repository detail fan out through `makes/bijux-py/` and `makes/packages/`

## First Proof Check

- `Makefile`
- `makes/README.md`

