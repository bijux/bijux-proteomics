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

What you can trust here is mostly the repo's honesty around missingness, QC,
and decision refusal. The repository does not currently earn a positive
outsider-auditable LFQ claim.

## Open First

- `benchmark:lfq_cohort_repeatability`
- `packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv`
- `packages/bijux-proteomics-core/tests/fixtures/quant/study_scale.design.tsv`
- `packages/bijux-proteomics-core/tests/fixtures/quant/quant_reproducibility_manifest.json`

## Current Trust Earned

- `outsider_review:lfq` is not complete enough to count as an outsider-auditable
  flagship family.
- benchmark evidence tier is `curated_mini_study`.
- public claim support is `refused`.
- the runtime package is still `quant_review-blocked-runtime-path`.
- the recommendation posture is `do_not_recommend`.
- the lab posture is `not_worth_assay`.

## Exact Claims

- LFQ review preserves study-design semantics, missingness visibility, and
  repeatable rollup behavior across the bundled fixture
- LFQ benchmark outputs can support review-grade abundance interpretation when
  QC and replicate caveats remain explicit

## What You Can Trust Right Now

- the repository will not hide missingness or QC weakness behind smooth summary
  prose
- the repo refuses stronger public support than the current comparator and
  runtime evidence deserve

## What You Should Not Trust Yet

- no flagship LFQ runtime family is wired
- comparator-backed public support is still refused
- this is not a flagship public LFQ package
