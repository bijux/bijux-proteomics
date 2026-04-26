---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency direction in `bijux-proteomics-intelligence` should make ownership more obvious as the package grows, not less. Imports that save a little time but hide who owns meaning are structural debt.

## Direction Rules

- consume contract and evidence inputs from neighboring packages without re-owning their semantics
- keep lab execution and runtime orchestration out of the decision layer
- treat reports and briefs as explanations of policy decisions, not as a second storage model

## First Proof Check

- imports in `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- package tests that exercise the seam
- neighboring handbooks when dependency pressure crosses a boundary
