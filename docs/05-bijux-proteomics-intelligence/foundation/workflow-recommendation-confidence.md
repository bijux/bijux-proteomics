---
title: Workflow Recommendation Confidence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-01
---

# Workflow Recommendation Confidence

`bijux-proteomics-intelligence` now ships one confidence bundle that keeps the
recommendation layer honest under withheld evidence.

## Why This Surface Matters

- confidence here is not a vibe score; it is a public record of where the
  recommendation layer would break if easy evidence disappeared
- this is one of the clearest places where the repository now shows real
  analytical seriousness instead of just cautious wording
- the bundle makes stronger recommendation language expensive because it must
  survive counterfactual loss, overconfidence review, and regret review

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

## How To Read The Current Bundle

- read the counterfactual report as the fastest test of whether the current
  sentence still depends on one missing evidence axis
- read the overconfidence audit as the place where public language is most at
  risk of sounding broader than the artifacts earn
- read the regret ledger as the maintainers' own admission of which workflow
  temptations still look too easy before hidden evidence lands

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

## What This Still Does Not Earn

- decision-grade authority for any current flagship family
- scientific truth independent of core and knowledge
- freedom from downstream lab burden once the consequence chain is read in full

## Combined Consequence Route

This page is not the full consequence chain by itself.

Open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
when the recommendation needs to be read beside contradiction pressure and lab
burden on one shared route.

Open [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
when the real question is which evidence loss or observed outcome moved the
call.

LFQ, PTM, and targeted still stop at bounded recommendation posture once the
full downstream consequence chain is included. None of them earns a
decision-grade recommendation sentence today.
