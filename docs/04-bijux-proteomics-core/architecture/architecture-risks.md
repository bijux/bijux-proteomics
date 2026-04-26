---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

Architecture risk in `bijux-proteomics-core` is mostly boundary risk: the package stops being obviously itself and starts carrying work that belongs elsewhere.

## Risk Pressure

- runtime-specific behavior leaks into core because it feels adjacent to execution contracts
- biology terms fork across modules and weaken the shared contract model
- downstream policy starts masquerading as a core invariant

## First Proof Check

- recent structural changes in the package
- tests and docs that still defend the original split
- neighboring handbook branches most likely to absorb the drift
