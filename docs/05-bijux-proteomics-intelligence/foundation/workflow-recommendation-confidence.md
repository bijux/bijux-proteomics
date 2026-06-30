---
title: Workflow Recommendation Confidence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-01
---

# Workflow Recommendation Confidence

This route answers the question after grounding: how strong may the current
recommendation sound once withheld evidence, comparator loss, and regret review
are taken seriously.

`bijux-proteomics-intelligence` owns this because recommendation confidence is
not a summary score. It is the pressure surface that stops attractive workflow
stories from sounding more certain than the shipped challenge artifacts earn.

## What Ships

The current confidence bundle is built around four public artifact families:

- counterfactual recommendation reports
- overconfidence audits
- underconfidence audits
- recommendation regret ledgers

Together they show how fragile the current public recommendation sentence still
is under evidence loss and hindsight review.

## What The Current Bundle Says

- all five flagship public families currently collapse toward
  `do_not_recommend` when comparator evidence is removed
- all five flagship public families currently collapse toward
  `do_not_recommend` when literature support is removed
- all five flagship public families currently collapse toward
  `do_not_recommend` when lab burden is doubled from the current shipped
  posture
- targeted currently carries the sharpest overconfidence pressure in the
  shipped bundle
- none of the current flagship families yet shows a hindsight-backed
  underconfidence event strong enough to justify broader public wording

## How To Read Recommendation Confidence

- read the counterfactual report first when the question is whether the current
  call survives one missing evidence axis
- read the overconfidence audit when the sentence sounds cleaner than the
  challenge surfaces justify
- read the regret ledger when the question is which kind of mistake maintainers
  are still most likely to make if hidden evidence is revealed later

## What This Means For Public Language

The current recommendation layer is materially more serious than it was at
`v0.3.7`, but it still does not earn decision-grade authority.

Why:

- the public sentence still breaks too easily under evidence removal
- some families still carry visible overconfidence pressure
- downstream assay burden still narrows otherwise attractive recommendation
  stories

That is why the stronger current product still needs bounded recommendation
language.

## Family-Level Reading

| family | confidence reading today | why the sentence still stays narrow |
| --- | --- | --- |
| `dda` | stronger than before, but still fragile under evidence removal | comparator and lab-burden loss still collapse the recommendation |
| `dia` | bounded outsider-facing recommendation support | evidence and consequence loss still narrow the call |
| `lfq` | real review-grade posture | missingness and transfer pressure still make the stronger sentence too expensive |
| `ptm` | stronger analytical posture than before | consequence confidence still lags localization strength |
| `targeted` | strongest current overconfidence pressure | calibration and interference risk still make broader certainty unsafe |

## Best Next Routes

- Open [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
  when the question is whether the sentence is supported at all.
- Open [Lab Consequence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lab-consequence/)
  when the question is whether downstream burden still narrows the apparently
  reasonable recommendation.
- Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the full combined route matters more than the recommendation layer by
  itself.

## Boundary

This page owns recommendation-pressure and confidence limits. It should not
pretend to replace evidence grounding or lab consequence just because those
later surfaces consume the recommendation output.
