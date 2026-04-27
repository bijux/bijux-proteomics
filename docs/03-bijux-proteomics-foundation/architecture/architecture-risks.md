---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

Architecture risk in `bijux-proteomics-foundation` is mostly boundary risk: the package stops being obviously itself and starts carrying work that belongs elsewhere.

## Risk Pressure

- shared types start carrying package-local policy
- serialization compatibility drifts faster than migration proof
- identifier meaning forks across consuming packages

## First Proof Check

- recent structural changes in the package
- tests and docs that still defend the original split
- neighboring handbook branches most likely to absorb the drift
