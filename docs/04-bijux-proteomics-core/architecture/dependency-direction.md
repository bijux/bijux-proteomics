---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `bijux-proteomics-core` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- pull shared meaning from foundation, but do not import intelligence or lab policy into the core contract layer
- keep runtime interaction behind explicit seams such as `runtime_adapter.py` and execution contracts
- treat biology and lifecycle helpers as contract logic, not as a dumping ground for orchestration convenience

## First Proof Check

- imports in `packages/bijux-proteomics-core/src/bijux_proteomics`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
