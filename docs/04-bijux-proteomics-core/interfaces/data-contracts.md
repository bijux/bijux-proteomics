---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts are the quickest way to judge whether a package really owns a concept or is just passing it through.

## Package Surface

- program and target schemas
- lifecycle and execution-contract payloads
- domain and biology-facing values that downstream packages interpret

## First Proof Check

- `src/bijux_proteomics/program_spec.py`, `programs.py`, and `targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli.py`
- `packages/bijux-proteomics-core/tests`
