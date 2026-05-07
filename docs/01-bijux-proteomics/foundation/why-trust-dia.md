---
title: Why Trust DIA
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Why Trust DIA

This page is about the current flagship `dia` result surface.

The right trust level is bounded. The repository can currently prove one
reviewable DIA import family with explicit capability limits. It cannot yet
pretend that this is a flagship outsider-readable public package on the same
level as DDA.

## Open First

- `benchmark:dia_library_extraction_consistency`
- `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv`
- `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_pipeline_export.tsv`
- `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`

## Current Trust Earned

- `outsider_review:dia` is inspectable, but not complete enough to count as an
  outsider-auditable flagship public package.
- benchmark evidence tier is `curated_mini_study`.
- public claim support is `advisory`.
- the runtime package `dia-diann-pipeline-corpus` is real and currently
  `import_only`.
- the recommendation posture is `recommend_with_downgrade`.
- the lab posture is `exploratory_only`.

## Exact Claims

- DIA adapter normalization preserves library-conditioned transition semantics
  across the pinned export corpus
- DIA review surfaces keep capability limits explicit instead of implying
  vendor-pipeline parity

## What You Can Trust Right Now

- the repo keeps DIA partial-support language explicit
- the DIA-NN and Spectronaut confrontation is visible instead of implied
- the runtime import lane is real enough to preserve lineage and artifact
  browsing

## What You Should Not Trust Yet

- this is still a `curated_mini_study`, not a flagship public package
- vendor-library parity is not earned
- broader raw-first DIA package realism is still missing
