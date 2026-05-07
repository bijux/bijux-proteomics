---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development guidance should protect package boundaries while making routine edits easier to review.

## Operating Rules

- change one knowledge concept at a time so evidence meaning does not drift silently
- run contradiction, confidence, and repository proof together when schemas move
- treat permissive fallback handling as a warning sign

## First Proof Check

- `src/bijux_proteomics_knowledge/memory/models/claims.py` and `memory/models/evidence.py`
- `src/bijux_proteomics_knowledge/memory/reconciliation/resolution.py` and `reviews/packets.py`
- `packages/bijux-proteomics-knowledge/tests`
