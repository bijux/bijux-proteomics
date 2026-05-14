---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development guidance should protect package boundaries while making routine edits easier to review.

## Operating Rules

- keep contract edits and downstream policy changes separate when possible
- run validation and schema proof alongside lifecycle changes
- stop when a local convenience edit starts changing durable meaning accidentally

## First Proof Check

- `src/bijux_proteomics/domain/program_spec.py` and `domain/targets.py`
- `src/bijux_proteomics/domain/lifecycle.py` and `domain/validation.py`
- `packages/bijux-proteomics-core/tests`
