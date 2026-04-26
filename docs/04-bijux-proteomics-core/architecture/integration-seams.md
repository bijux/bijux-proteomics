---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `bijux-proteomics-core` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- foundation supplies shared ids and schema meaning
- runtime consumes core contracts but should not rewrite them
- intelligence and lab packages build on these rules without owning them

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
