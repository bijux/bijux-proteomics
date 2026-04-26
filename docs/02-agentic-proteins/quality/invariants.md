---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Invariants

Invariants are the claims that must remain true for the package to stay worth trusting.

## Review Rules

- legacy public paths must still map to the intended canonical runtime behavior
- the bridge must not become the place where new strategic features are born
- compatibility state and artifacts must stay inspectable enough to justify retirement later

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `api/app.py`
- `src/agentic_proteins/runtime/`
