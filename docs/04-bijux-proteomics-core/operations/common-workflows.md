---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- review a program or target contract change against lifecycle and execution rules
- check whether runtime consumers need explicit downstream validation
- update contract-facing docs with the same discipline as the code change

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`
