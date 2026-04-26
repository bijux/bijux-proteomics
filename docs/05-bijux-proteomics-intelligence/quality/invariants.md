---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Invariants

Invariants are the claims that must remain true for the package to stay worth trusting.

## Review Rules

- recommendations must stay explainable through candidates, policies, evaluators, and outputs
- decision logic must not re-own evidence semantics or lab execution behavior
- public reports and outcomes must continue to justify why the system moved

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/policies.py` and `evaluators.py`
- `src/bijux_proteomics_intelligence/report/` and `outcomes.py`
