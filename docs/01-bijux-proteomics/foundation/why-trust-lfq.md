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
