---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility commitments are expensive promises. They should be visible enough that nobody expands them by accident.

## Package Surface

- public core contracts should change cautiously and with visible downstream review
- CLI or schema shifts that alter contract meaning require explicit validation proof
- downstream convenience should not outrank contract stability

## First Proof Check

- `src/bijux_proteomics/program_spec.py`, `programs.py`, and `targets.py`
- `src/bijux_proteomics/cli.py` and `interfaces/cli.py`
- `packages/bijux-proteomics-core/tests`
