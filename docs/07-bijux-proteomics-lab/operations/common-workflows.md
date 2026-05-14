---
title: Common Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Common Workflows

Common workflows should sound like the real jobs people do with the package, not generic process filler.

## Operating Rules

- review how recommended work becomes an assay plan or promoted outcome
- check downstream consumers of lab records before calling a payload change safe
- update operator examples when plan or promotion behavior changes

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
