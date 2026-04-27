---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Error Model

Failures in `bijux-proteomics-foundation` should help a reviewer tell whether the problem is local, upstream, downstream, or a boundary mismatch. Error handling that hides ownership makes the package harder to trust.

## Error Rules

- shared failures should say the payload meaning is invalid, incomplete, or incompatible
- do not hide migration breakage inside permissive coercion
- do not encode downstream policy failures in the shared error model

## First Proof Check

- package error types and failure paths
- tests that assert the intended failure class
- neighboring packages when a failure crosses a handoff seam
