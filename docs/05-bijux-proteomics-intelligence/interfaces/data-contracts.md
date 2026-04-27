---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Data Contracts

Data contracts are the quickest way to judge whether a package really owns a concept or is just passing it through.

## Package Surface

- candidate and metric payloads
- evaluation, outcome, and report shapes
- inputs and outputs that downstream packages use to act on a recommendation

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates.py`, `policies.py`, and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, and `outcomes.py`
- `packages/bijux-proteomics-intelligence/tests`
