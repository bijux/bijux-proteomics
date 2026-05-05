---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# API Surface

An API surface is only real when the package actually owns the network-facing contract, not when docs are trying to look complete.

## Package Surface

- this package is primarily consumed through Python contracts rather than a standalone HTTP API
- service APIs should be built by runtime or other operator-facing packages on top of core meanings
- if a network shape appears here, it should still read like a contract export rather than a service product

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli/app.py`
- `packages/bijux-proteomics-core/tests`
