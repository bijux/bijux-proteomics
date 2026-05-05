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

## Invariant Model

```mermaid
flowchart LR
    recommendation["recommendation meaning stays explainable"]
    ownership["decision logic does not re-own evidence or lab behavior"]
    outputs["reports and outcomes justify why the system moved"]

    recommendation --> ownership --> outputs
```

This page should make intelligence invariants feel like explanation constraints.
The package is only worth trusting if recommendation movement can still be
reconstructed from policy, evaluation, and report surfaces.

## Review Rules

- recommendations must stay explainable through candidates, judgment, posture, and outputs
- decision logic must not re-own evidence semantics or lab execution behavior
- public reports and outcomes must continue to justify why the system moved

## First Proof Check

- `packages/bijux-proteomics-intelligence/tests`
- `src/bijux_proteomics_intelligence/candidates/`, `judgment/`, and `posture/`
- `src/bijux_proteomics_intelligence/reviews/`, `interpretation/`, and `learning/`

## Design Pressure

Intelligence invariants fail when recommendation behavior drifts faster than
the system can explain it. The package has to keep decision ownership and
explanatory output tightly coupled.
