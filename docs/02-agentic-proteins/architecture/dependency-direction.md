---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `agentic-proteins` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- depend inward on lower shared packages and outward on the canonical runtime only when the bridge has to preserve an existing surface
- reject new coupling that makes modern packages depend on the legacy bridge for fresh behavior
- treat compatibility shims as temporary structure, not a place to centralize new orchestration

## First Proof Check

- imports in `packages/agentic-proteins/src/agentic_proteins`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
