---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `bijux-proteomics-lab` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- intelligence hands recommended work into lab execution
- core and foundation supply shared contracts and identifiers
- runtime may execute work around the lab package without owning its decision semantics

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
