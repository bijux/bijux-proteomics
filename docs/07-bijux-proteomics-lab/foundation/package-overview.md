---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-lab` owns assay consequence: readiness checks, control
demands, material and queue burden, handoff honesty, and the observed outcomes
that later tighten the upstream story. The package is only healthy when those
downstream decisions stay distinct from scientific truth, recommendation
policy, and runtime execution control.

## What It Owns

- plan assay work with explicit burden, readiness, and control requirements
- capture observed outcomes against requested work and blocked work alike
- publish honest handoffs, refusal surfaces, and follow-up consequence records

## What It Refuses

- evidence truth or contradiction resolution
- recommendation policy or ranking posture
- general execution orchestration, replay, or provider control

## First Proof Check

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab`
- `packages/bijux-proteomics-lab/tests`
- neighboring handbook branches once a change crosses the local role
