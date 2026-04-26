---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `bijux-proteomics-foundation` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- all downstream packages consume foundation meaning and should agree on it
- repository release and migration review use foundation as the compatibility baseline
- foundation should not decide scientific, recommendation, evidence, or lab policy on behalf of a consumer

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
