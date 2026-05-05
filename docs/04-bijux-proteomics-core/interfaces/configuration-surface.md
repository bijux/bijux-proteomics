---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration belongs in the public surface only when a reader must understand it to use the package safely.

## Package Surface

- contract and validation options that shape readiness rules
- runtime-adapter settings only where they express contract-level intent
- schema-version expectations carried through serialization surfaces

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli/app.py`
- `packages/bijux-proteomics-core/tests`
