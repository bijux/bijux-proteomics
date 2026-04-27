---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Local Development

Local development guidance should protect package boundaries while making routine edits easier to review.

## Operating Rules

- edit planning or outcome paths in small, reviewable steps
- run repository and serialization proof whenever a lab payload changes
- stop when a local change starts redefining upstream recommendation meaning

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py`
- `src/bijux_proteomics_lab/repositories.py` and `serialization.py`
- `packages/bijux-proteomics-lab/tests`
