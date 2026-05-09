---
title: This Package Does Not Own
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-05-09
---

# This Package Does Not Own

Package: `bijux-proteomics-lab`  
Import root: `bijux_proteomics_lab`

Lab owns assay consequence, readiness, and observed follow-up. It should make
burden and control demands explicit without taking over upstream scientific or
runtime authority.

## Supported Package-Root Imports

- `plan_experiment_batches`
- `build_advisory_assay_plan`
- `build_executable_assay_plan`

## Allowed Package Dependencies

- `bijux-proteomics-core`
- `bijux-proteomics-foundation`
- `bijux-proteomics-intelligence`
- `bijux-proteomics-knowledge`

Lab may consume scientific intent, recommendation posture, and evidence
support, but it should stay the owner of operational feasibility and traceable
follow-up.

## Excluded Responsibilities

- analytical recommendation logic
- core scientific semantics
- execution orchestration or runtime policy

## Route Elsewhere

- Use `bijux-proteomics-intelligence` when the work changes recommendation
  strength, refusal posture, or ranking policy.
- Use `bijux-proteomics-core` when the work changes lifecycle truth, scientific
  semantics, or workflow contracts.
- Use `bijux-proteomics-runtime` when the work changes provider execution,
  replay, or operator-facing runtime behavior.
