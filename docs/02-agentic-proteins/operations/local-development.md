---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development guidance should protect package boundaries while making routine edits easier to review.

## Operating Rules

- change the bridge with the canonical runtime diff open beside it
- run the smallest compatibility proof that shows whether the forwarding contract still holds
- stop if local edits start creating new long-term behavior in the bridge

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/` and `providers/`
- `packages/agentic-proteins/tests`
