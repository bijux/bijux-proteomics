---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `bijux-proteomics-knowledge` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- depend on shared contract meaning without inheriting downstream policy choices
- keep recommendation scoring out of the knowledge layer even when evidence quality affects later decisions
- treat repository and serialization helpers as storage boundaries, not as authority over runtime behavior

## First Proof Check

- imports in `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
