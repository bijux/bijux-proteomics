---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Error Model

Failures in `bijux-proteomics-core` should help a reviewer tell whether the problem is local, upstream, downstream, or a boundary mismatch. Error handling that hides ownership makes the package harder to trust.

## Error Rules

- contract and readiness failures should be explicit and reviewable
- domain-validation errors should stay separate from runtime transport failures
- error names should help a reviewer tell whether the failure is semantic, structural, or procedural

## First Proof Check

- package error types and failure paths
- tests that assert the intended failure class
- neighboring packages when a failure crosses a handoff seam
