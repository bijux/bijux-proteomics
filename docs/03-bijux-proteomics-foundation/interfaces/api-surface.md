---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# API Surface

An API surface is only real when the package actually owns the network-facing contract, not when docs are trying to look complete.

## Package Surface

- this package does not publish a standalone HTTP API surface
- network contracts should be expressed through consuming packages that use foundation types
- if an API seems to belong here, check whether the real need is shared schema rather than a service surface

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py`
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py`
- `packages/bijux-proteomics-foundation/tests`
