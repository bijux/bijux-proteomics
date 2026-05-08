---
title: Workflow Recommendation Confidence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-05-08
---

# Workflow Recommendation Confidence

`bijux-proteomics-intelligence` now ships one confidence bundle that keeps the
recommendation layer honest under withheld evidence.

## What Ships

- one counterfactual recommendation report at
  `artifacts/intelligence/benchmark-decisions/counterfactual_recommendations.json`
- one overconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_overconfidence_audit.json`
- one underconfidence audit at
  `artifacts/intelligence/benchmark-decisions/workflow_underconfidence_audit.json`
- one regret ledger at
  `artifacts/intelligence/benchmark-decisions/recommendation_regret_ledger.json`

## What The Current Surfaces Say

- all five flagship families currently collapse to `do_not_recommend` if
  comparator evidence is removed
- all five flagship families currently collapse to `do_not_recommend` if
  literature evidence is removed
- all five flagship families currently collapse to `do_not_recommend` if lab
  burden doubles from the current shipped posture
- targeted currently carries the strongest overconfidence score at `0.67`
- the other four current flagship families each carry an overconfidence score
  of `0.5`
- no workflow family currently shows a hindsight-backed underconfidence event

## What The Regret Ledger Captures

The regret ledger is not prose perfume.

It records the patterns maintainers would most want to undo after the hidden
evidence is revealed:

- targeted: letting a follow-up stay alive until hidden interference and
  carryover evidence force a miss
- dda, dia, lfq, ptm: letting one attractive family claim sound stronger than
  the paired-package reveal earns

## Why This Matters

These surfaces make stronger intelligence authority expensive.

If the package wants to sound more certain in public, it now has to survive the
blinded challenge results, the counterfactual collapses, and the regret ledger
without hiding where the current recommendation posture still breaks.
