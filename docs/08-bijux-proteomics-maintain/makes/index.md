---
title: makes
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# makes

The `makes/` section explains the shared command surface that ties local work,
CI validation, package dispatch, and release-oriented automation together.

The make layer is a real repository interface. These pages exist so a
maintainer can trace a command from `Makefile` to the fragment that owns it
without having to reverse-engineer the whole tree from includes alone.

## Pages In This Section

- [Make System Overview](make-system-overview.md)
- [Root Entrypoints](root-entrypoints.md)
- [Environment Model](environment-model.md)
- [Repository Layout](repository-layout.md)
- [Package Dispatch](package-dispatch.md)
- [CI Targets](ci-targets.md)
- [Package Contracts](package-contracts.md)
- [Release Surfaces](release-surfaces.md)
- [Authoring Rules](authoring-rules.md)

## Purpose

This page routes maintainers into the make-system documentation without forcing
them to infer structure from file names alone.

## Stability

Keep it aligned with the make surfaces that the repository actually exposes.
