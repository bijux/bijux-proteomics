---
title: Make System Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Make System Overview

The repository make system is the shared command language for maintainer work.

It starts at `Makefile`, delegates to `makes/root.mk`, and then pulls in
repository fragments, reusable `bijux-py` contracts, package dispatch, and
per-package bindings. The structure matters because it keeps command ownership
traceable instead of burying it in one oversized file.

## Core Shape

- `Makefile` is the top-level entrypoint
- `makes/root.mk` assembles repository-wide includes
- `makes/bijux-py/` carries reusable command contracts and target families
- `makes/packages/` maps those shared contracts onto real proteomics packages

## Purpose

This page gives the shortest honest explanation of how the make system is
organized.

## Stability

Keep it aligned with the actual include structure rooted at `Makefile`.
