---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Dependencies and Adjacencies

`bijux-proteomics-foundation` should depend on neighboring packages only in ways that strengthen
its role as shared payload meaning. Adjacency is acceptable when it clarifies handoff and
unacceptable when it lets the package silently absorb a neighbor's job.

## Review Rule

- depend downward for prerequisites you genuinely need
- hand off upward or sideways when another package owns the meaning
- reject convenience coupling that makes the package harder to defend

## First Proof Check

- the imports and public contracts in `packages/bijux-proteomics-foundation`
- neighboring handbook branches when a dependency starts carrying meaning
