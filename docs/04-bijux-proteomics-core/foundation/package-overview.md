---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-core` exists to define durable program contracts, lifecycle rules, and gate semantics used by downstream layers. The package is useful only when that
role stays narrow enough that a reviewer can say why it exists without naming
several different owners at once.

## What It Owns

- define program specifications and lifecycle state
- encode gates and operating constraints
- publish stable core contracts to downstream packages

## What It Refuses

- shared schema primitives
- evidence truth
- operator-facing runtime execution

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- neighboring handbook branches once a change crosses the local role
