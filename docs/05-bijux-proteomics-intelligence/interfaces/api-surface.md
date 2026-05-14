---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# API Surface

An API surface is only real when the package actually owns the network-facing contract, not when docs are trying to look complete.

## Package Surface

- this package does not present a standalone network API as its primary contract
- public service endpoints should be composed by runtime or application layers that consume intelligence outputs
- if an API change is proposed here, check whether the real contract is a report or outcome payload instead

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates/`, `judgment/`, and `posture/`
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/`
- `packages/bijux-proteomics-intelligence/tests`
