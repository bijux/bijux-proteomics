---
title: Quality Gates
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Quality Gates

Quality gates in this package should block repository drift before it reaches release or public docs.

## Gate Rules

- keep architecture, dependency, and contract checks explicit
- prefer failing with a named policy reason over silent lenience
- make every gate traceable to checked-in helper code and tests

## First Proof Check

- `src/bijux_proteomics_dev/quality/`
- `packages/bijux-proteomics-dev/tests`

