---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Error Model

Failures in `bijux-proteomics-intelligence` should help a reviewer tell whether the problem is local, upstream, downstream, or a boundary mismatch. Error handling that hides ownership makes the package harder to trust.

## Error Rules

- separate invalid inputs from policy conflicts and evaluator failures
- make explainability gaps visible instead of silently returning a recommendation
- do not mask evidence uncertainty as a scoring success

## First Proof Check

- package error types and failure paths
- tests that assert the intended failure class
- neighboring packages when a failure crosses a handoff seam
