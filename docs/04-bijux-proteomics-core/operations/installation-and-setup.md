---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

Setup should get a reader to the package proof surface quickly instead of reproducing the whole repository in miniature.

## Operating Rules

- local setup should get a reviewer quickly to contract and lifecycle proof
- prefer schema, CLI, and test paths that expose readiness and execution rules directly
- avoid bundling runtime or policy-heavy setup into the core review loop

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`
