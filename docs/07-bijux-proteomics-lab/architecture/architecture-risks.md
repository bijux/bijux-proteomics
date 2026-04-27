---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

Architecture risk in `bijux-proteomics-lab` is mostly boundary risk: the package stops being obviously itself and starts carrying work that belongs elsewhere.

## Risk Pressure

- recommendation policy leaks into the lab layer because handoff is weakly defined
- repository helpers silently become the place where domain meaning changes
- lab-specific payloads fork from shared contracts and become harder to migrate

## First Proof Check

- recent structural changes in the package
- tests and docs that still defend the original split
- neighboring handbook branches most likely to absorb the drift
