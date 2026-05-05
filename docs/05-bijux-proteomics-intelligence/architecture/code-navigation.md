---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Code Navigation

Code navigation should get a reviewer from the package question to the owning module family quickly. If the only way to navigate `bijux-proteomics-intelligence` is by private memory, the docs are not doing enough.

## Start Here

- `src/bijux_proteomics_intelligence/candidates/` for candidate inputs and quality framing
- `src/bijux_proteomics_intelligence/judgment/` and `posture/` for scoring, refusal, and recommendation structure
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/` for explanation, analytical projections, and refinement control

## First Proof Check

- the source tree in `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- package tests for the same concern
- neighboring package docs when the local tree stops being enough
