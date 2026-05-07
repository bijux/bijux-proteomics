---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Recovery guidance should help maintainers restore the right behavior, not just any working state.

## Operating Rules

- recover by restoring a valid plan or outcome state before adding local exceptions
- separate repository failures from upstream recommendation ambiguity
- treat bad promotions as incidents because they alter durable lab history

## First Proof Check

- `src/bijux_proteomics_lab/planning/assays.py`, `planning/scheduling.py`, and `outcomes/observations.py`
- `src/bijux_proteomics_lab/reconciliation/follow_up.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
