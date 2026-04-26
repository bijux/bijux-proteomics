---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `bijux-proteomics-intelligence` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- core defines the contract substrate that intelligence evaluates
- knowledge supplies evidence and contradiction context
- lab receives recommended work and should remain a separate execution owner

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
