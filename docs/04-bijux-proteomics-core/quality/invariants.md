---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Invariants

Invariants are the claims that must remain true for the package to stay worth trusting.

## Review Rules

- program, target, and lifecycle meanings remain explicit
- core owns contract semantics without absorbing runtime or policy decisions
- schema and validation surfaces move together when durable meaning changes

## First Proof Check

- `packages/bijux-proteomics-core/tests`
- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
