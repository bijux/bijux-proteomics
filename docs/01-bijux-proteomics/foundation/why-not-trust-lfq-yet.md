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
- no flagship runtime benchmark path is wired for this workflow family yet
- public comparator-backed claim support is still refused
- biological grounding remains thin
- comparator drift or missing external execution parity still materially limits
  this public workflow claim

## What Would Need To Change

- add stronger external quant comparator pressure so repeatability and
  effect-size claims are not inferred from fixture stability alone
- add a flagship LFQ runtime family instead of leaving the workflow at
  `quant_review-blocked-runtime-path`
- harden biological grounding until the current public package is enough to
  support stronger recommendation and release posture
