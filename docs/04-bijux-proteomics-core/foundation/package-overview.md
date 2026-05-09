---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-core` owns the durable scientific contracts that the rest of
the repository depends on: program, target, assay, and review entities;
lifecycle transitions; review gates; normalized proteomics I/O seams; and
benchmark-acceptance surfaces. The package is only healthy when those
scientific rules remain runtime-agnostic and distinct from evidence memory,
recommendation posture, and assay consequence.

## What It Owns

- define program, target, assay, and review entities
- encode lifecycle transitions, gate truth, and runtime-agnostic workflow
  requests
- publish benchmark-acceptance and scientific contract surfaces to downstream
  packages

## What It Refuses

- shared schema primitives that belong in foundation
- evidence memory, contradiction handling, or recommendation policy
- operator-facing runtime execution, replay, or assay-consequence ownership

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- neighboring handbook branches once a change crosses the local role
