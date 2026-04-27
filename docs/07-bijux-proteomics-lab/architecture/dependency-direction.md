---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `bijux-proteomics-lab` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- consume recommendation and evidence inputs without re-owning scoring or knowledge semantics
- keep shared meaning in foundation and durable program contracts in core instead of copying them locally
- treat repositories as lab state boundaries, not as generic execution infrastructure

## First Proof Check

- imports in `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
