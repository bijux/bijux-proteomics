---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `bijux-proteomics-knowledge` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- intelligence consumes knowledge outputs but should not redefine them
- runtime may persist or transport this data without owning its semantics
- lab and core can reference knowledge state through explicit contracts only

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
