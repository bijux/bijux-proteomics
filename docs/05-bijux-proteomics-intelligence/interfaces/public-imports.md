---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Public Imports

Public imports should make it obvious which modules are safe to rely on and which ones are just nearby implementation detail.

## Package Surface

- `bijux_proteomics_intelligence.candidates`, `judgment`, and `posture` for decision logic imports
- `bijux_proteomics_intelligence.reviews` and `interpretation` for reviewer-facing analytical outputs
- `bijux_proteomics_intelligence.learning` and `governance` for adaptation and charter surfaces

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates/`, `judgment/`, and `posture/`
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/`
- `packages/bijux-proteomics-intelligence/tests`
