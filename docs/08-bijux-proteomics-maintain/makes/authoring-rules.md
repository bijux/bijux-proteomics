---
title: Authoring Rules
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-10
---

# Authoring Rules

The make layer stays maintainable only when new fragments follow the same
structural discipline as the existing tree.

## Rules

- put shared logic in the narrowest reusable fragment that can honestly own it
- keep package bindings thin and descriptive
- prefer explicit variables and includes over hidden shell indirection
- place CI-only logic in the CI fragment family instead of spreading it across
  unrelated targets
- document new make surfaces in this handbook when they become part of the
  repository contract

## Purpose

This page records the authoring discipline that keeps the make system coherent.

## Stability

Update it when the repository’s actual make authoring rules change.
