---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility commitments are expensive promises. They should be visible enough that nobody expands them by accident.

## Package Surface

- decision outputs should stay explainable across change
- report and outcome shapes are public enough to deserve deliberate migration review
- new policy knobs should not create silent meaning drift

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates.py`, `policies.py`, and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
