---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security guidance should protect the package boundary as well as the code path itself.

## Operating Rules

- security fixes should preserve the runtime handoff rather than fork it
- treat stale compatibility surfaces as security liabilities when they prolong unnecessary exposure
- do not add bridge-only secret or provider handling without runtime-owner review

## First Proof Check

- `src/agentic_proteins/interfaces/cli.py` and `interfaces/http/app.py`
- `src/agentic_proteins/execution/`, `state/`, and `providers/`
- `packages/agentic-proteins/tests`
