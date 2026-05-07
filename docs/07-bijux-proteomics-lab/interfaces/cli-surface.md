---
title: CLI Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# CLI Surface

CLI documentation should describe the commands the package truly owns, not the commands a reader might wish existed.

## Package Surface

- there is no standalone CLI product owned directly by this package
- operator workflows should be described through contract examples or downstream tooling that invokes lab behavior
- do not invent command surfaces that imply the lab package also owns runtime orchestration

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/design/protocols.py`, `handoffs/artifacts.py`, and `handoffs/serialization.py`
- `packages/bijux-proteomics-lab/tests`
