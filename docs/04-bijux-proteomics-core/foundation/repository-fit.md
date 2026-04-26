---
title: Repository Fit
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Repository Fit

This package anchors rules that should remain stable even as evidence, scoring, or execution layers evolve.

## Fit Test

A package fits the repository only when its role is narrower than the system
and clearer than a generic utility bucket. If the package cannot justify why it
exists separately, the split is drifting.

## First Proof Check

- the package handbook root
- the package source tree and tests
- neighboring package handbooks that would absorb the behavior if the fit claim
  were false
