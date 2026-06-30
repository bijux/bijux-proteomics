---
title: Why Trust LFQ
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Why Trust LFQ

This page is about the current flagship `lfq` surface.

What you can trust here is the repo's honesty around missingness, QC, and
bounded cohort interpretation across two public LFQ packages plus one published
cross-package report. The repository earns a bounded outsider-auditable LFQ
claim, not broad cohort-transfer or decision-grade quant authority.

## Open First

- `benchmark:lfq_cohort_repeatability`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/quality_sheet.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`

## Current Trust Earned

- `outsider_review:lfq` is complete enough to count as an outsider-auditable
  flagship family.
- benchmark evidence tier is `external_reproduction_package`.
- public claim support is `advisory`.
- the runtime package is now `lfq-cohort-review-corpus`.
- the companion family-transfer report is currently `highly_stable` at `0.84`,
  but effect-direction confidence weakens on the sparse contrast package.
- the recommendation posture is `recommend_with_downgrade`.
- the lab posture is `exploratory_only`.
- decision-grade wording remains blocked because the shared consequence chain
  still ends at exploratory-only follow-up and can collapse under higher assay
  burden.

## Exact Claims

- LFQ review preserves study-design semantics, missingness visibility, and
  repeatable rollup behavior across the bundled cohort package
- LFQ benchmark outputs can support review-grade abundance interpretation when
  QC and replicate caveats remain explicit

## What You Can Trust Right Now

- the repository will not hide missingness or QC weakness behind smooth summary
  prose
- the repo keeps comparator and generalization limits visible instead of
  flattening the current package into universal cohort truth
- the tracked public package keeps cohort design, feature evidence, and package
  lifecycle visible instead of implied
- the runtime bundle now shows normalization, missingness, differential, and
  review outputs as one checked flagship run family
- the companion sparse-contrast package publishes a second family-transfer check
  at
  `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`

## What You Should Not Trust Yet

- comparator drift or missing external execution parity still materially limits
  this public workflow claim
- effect-direction confidence weakens on the sparse companion cohort
- broad generalization beyond the two current cohort packages is not earned

## Consequence Boundary

- open [Workflow Consequence Maps](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-consequence-maps/)
  before widening LFQ language beyond a bounded recommendation
- open [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/)
  before claiming that one extra cohort or follow-up loop materially changed the
  call
- open [Workflow Refusal Handbook](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook/)
  when the next honest move may still be stop, rerun, narrow, or refuse
- one doubled assay burden or one weak observed outcome still demotes the
  public sentence faster than this page alone might suggest

## Evidence Grounding

- sentence grounding and unsupported-claim review:
  [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
- citation freshness, bibliography export, and gap audits:
  [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/)
