---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Test Strategy

A useful test strategy names what evidence is needed and why shallow coverage is not enough.

## Review Rules

- favor contract, lifecycle, and schema tests that explain the rule being defended
- cover runtime-adjacent seams where downstream drift is most likely
- prefer targeted proof of durable meaning over broad but vague regression suites

## First Proof Check

- `packages/bijux-proteomics-core/tests`
- `src/bijux_proteomics/program_spec.py` and `targets.py`
- `src/bijux_proteomics/lifecycle.py` and `validation.py`
