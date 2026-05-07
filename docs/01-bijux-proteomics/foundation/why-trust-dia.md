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

The right trust level is bounded. The repository now ships two public DIA
packages plus one published cross-package report, so a reviewer can inspect
whether DIA trust survives beyond one library-conditioned package. The
authority still stops at library-conditioned review rather than
vendor-execution parity.

## Open First

- `benchmark:dia_library_extraction_consistency`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/README.md`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`

## Current Trust Earned

- `outsider_review:dia` is complete enough to count as an outsider-auditable
  flagship family.
- benchmark evidence tier is `external_reproduction_package`.
- public claim support is `advisory`.
- the runtime package `dia-diann-pipeline-corpus` is real and currently
  `raw_executable`.
- the companion family-transfer report is currently `highly_stable` at `0.83`,
  but protein-level absence language still weakens on the second package.
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
- the runtime lane is raw-executable enough to preserve lineage and artifact
  browsing without stopping at an import-only bridge
- the tracked public package makes artifact inventory, quality posture, and
  lifecycle boundaries inspectable without reading internal code
- the companion matrix-shift package publishes a second family-transfer check at
  `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`

## What You Should Not Trust Yet

- vendor-library parity is not earned
- chromatogram-level and vendor-execution parity are not earned
- the current reproduction story still depends on execution steps outside the
  repository proof boundary
- protein-level absence claims stay downgrade-heavy because the second package
  weakens them materially
