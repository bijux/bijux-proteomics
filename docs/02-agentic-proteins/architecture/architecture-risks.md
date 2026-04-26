---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

Architecture risk in `agentic-proteins` is mostly boundary risk: the package stops being obviously itself and starts carrying work that belongs elsewhere.

## Risk Pressure

- the bridge becomes a second permanent runtime instead of shrinking
- legacy compatibility code diverges from the canonical runtime path
- new work lands here because the old surface feels convenient

## First Proof Check

- recent structural changes in the package
- tests and docs that still defend the original split
- neighboring handbook branches most likely to absorb the drift
