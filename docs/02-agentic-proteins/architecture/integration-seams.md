---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams matter because `agentic-proteins` is not allowed to explain the whole system by itself. The package has to cooperate with neighbors while staying narrow enough to defend.

## Major Seams

- `bijux-proteomics-runtime` is the canonical execution neighbor and should receive new behavior instead of the bridge
- lower packages still own scientific meaning, shared contracts, and recommendation semantics
- legacy callers remain a compatibility seam, not a design center

## First Proof Check

- code that crosses the seam
- tests that pin the seam behavior
- both handbook branches when the seam changes
