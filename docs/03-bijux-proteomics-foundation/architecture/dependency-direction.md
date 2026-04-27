---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `bijux-proteomics-foundation` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- stay dependency-light so shared meaning can travel across all packages without dragging policy or workflow code with it
- allow downstream packages to import foundation, but reject reverse imports that would pull package-specific semantics back into the shared layer
- treat versioned migration helpers as shared infrastructure, not as a place for business logic

## First Proof Check

- imports in `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
