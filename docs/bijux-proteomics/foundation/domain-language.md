---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Domain Language

Stable language is part of the repository design.

When terms drift, readers stop knowing whether they are talking about a package
contract, a repository rule, or a maintainer-only concern. That confusion
rebuilds architectural blur even when the tree still looks tidy.

## Terms That Should Stay Stable

- `repository handbook` for cross-package governance and structure
- `maintainer handbook` for repository-health automation and operations
- `canonical package` for one of the publishable product distributions
- `proof surface` for the files that let a reader verify a claim, such as
  tests, schema artifacts, metadata, or workflow definitions

## Purpose

This page records vocabulary that should remain consistent across docs, code,
metadata, and review conversations.

## Stability

Change it only when the repository meaning of a term actually changes.
