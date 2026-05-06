---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Operator workflows should say who uses the surface, why they use it, and when they should stop and open a neighbor handbook instead.

## Package Surface

- developers checking whether a change belongs in durable contract space
- runtime integrators consuming core execution rules
- reviewers validating that contract outputs remain stable

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py`, `domain/repositories.py`, and `domain/targets.py`
- `src/bijux_proteomics/interfaces/cli/app.py` and `interfaces/cli/__main__.py`
- `packages/bijux-proteomics-core/tests`
