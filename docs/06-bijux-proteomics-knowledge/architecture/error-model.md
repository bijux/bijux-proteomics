---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Error Model

Failures in `bijux-proteomics-knowledge` should help a reviewer tell whether the problem is local, upstream, downstream, or a boundary mismatch. Error handling that hides ownership makes the package harder to trust.

## Error Rules

- surface contradictions, incomplete evidence, and invalid review state explicitly
- keep trust-model failures distinct from storage or transport failures
- do not smooth over unresolved evidence conflict for the sake of downstream convenience

## First Proof Check

- package error types and failure paths
- tests that assert the intended failure class
- neighboring packages when a failure crosses a handoff seam
