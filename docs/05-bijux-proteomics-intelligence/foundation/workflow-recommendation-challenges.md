---
title: Workflow Recommendation Challenges
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-05-08
---

# Workflow Recommendation Challenges

`bijux-proteomics-intelligence` now ships blinded recommendation challenge
surfaces for the five flagship workflow families that currently carry outsider
recommendation posture.

The point is simple:
the package should publish what the recommendation layer chose before hidden
companion-package or perturbation evidence was revealed, and then publish
whether that choice landed as a hit, a miss, or an overconfidence signal.

## What Ships

- one blinded recommendation challenge per flagship family:
  `dda_blinded_recommendation_challenge.json`,
  `dia_blinded_recommendation_challenge.json`,
  `lfq_blinded_recommendation_challenge.json`,
  `ptm_blinded_recommendation_challenge.json`,
  `targeted_blinded_recommendation_challenge.json`
- one cross-family overconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_overconfidence_audit.json`
- one cross-family underconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_underconfidence_audit.json`

## Current Family Outcomes

- `dda`: `1` hit, `1` overconfidence, `0` misses
- `dia`: `1` hit, `1` overconfidence, `0` misses
- `lfq`: `1` hit, `1` overconfidence, `0` misses
- `ptm`: `1` hit, `1` overconfidence, `0` misses
- `targeted`: `1` hit, `1` overconfidence, `1` miss

The targeted miss matters most right now.
The hidden interference and carryover perturbation collapses the follow-up lane
that still looks actionable when only the cleaner decision brief is visible.

## Why This Belongs Here

These surfaces are intelligence work rather than core or knowledge work.

The benchmark packages, literature surfaces, and contradiction dossiers still
own truth.
This package owns what the recommendation layer does with those surfaces when
it must choose, stay bounded, or refuse.
