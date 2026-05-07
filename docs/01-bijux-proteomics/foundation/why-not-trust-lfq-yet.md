---
title: Why Not Trust LFQ Yet
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Why Not Trust LFQ Yet

`lfq` is still blocked from flagship outsider-auditable status.

## Current Blockers

- a real LFQ public package exists, but it still stops short of outsider-auditable
  authority
- the runtime family now exists as `lfq-cohort-review-corpus`, but runtime
  execution alone does not repair the missing comparator and grounding gaps
- public comparator-backed claim support is still refused
- biological grounding remains thin
- comparator drift or missing external execution parity still materially limits
  this public workflow claim

## What Would Need To Change

- add stronger external quant comparator pressure so repeatability and
  effect-size claims are not inferred from fixture stability alone
- harden biological grounding until the current public package is enough to
  support stronger recommendation and release posture
