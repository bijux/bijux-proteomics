---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Error Model

Failures in `agentic-proteins` should help a reviewer tell whether the problem is local, upstream, downstream, or a boundary mismatch. Error handling that hides ownership makes the package harder to trust.

## Error Rules

- preserve caller-visible compatibility behavior where retirement is not complete
- translate failures toward the canonical runtime model instead of inventing a separate long-term error taxonomy
- make migration-specific failures obvious so stale compatibility promises can be retired safely

## First Proof Check

- package error types and failure paths
- tests that assert the intended failure class
- neighboring packages when a failure crosses a handoff seam
