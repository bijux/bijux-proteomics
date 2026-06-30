---
title: Why Trust DIA
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Why Trust DIA

This page is about the current flagship `dia` result surface.

The right trust level is bounded. The repository now ships two public DIA
packages plus one published cross-package report, so a reviewer can inspect
whether DIA trust survives beyond one library-conditioned package. The
authority still stops at library-conditioned review rather than
vendor-execution parity.

The meaningful change since `v0.3.7` is that DIA now sits on a clearer chain of
runtime, grounding, recommendation, and consequence surfaces. The boundary is
still real: stronger public packets do not yet become chromatogram-level or
vendor-parity authority.

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

## What The Reader Is Really Auditing

- whether library-conditioned DIA evidence stays inspectable across the primary
  and companion packages
- whether the raw-executable runtime lane preserves rerun trust instead of
  outsourcing it to maintainer narration
- whether absent-peptide and matrix-shift pressure remain visible in the final
  sentence

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

## Why The Public Sentence Still Narrows

- library incompleteness still limits broader biological confidence
- absent-peptide reasoning weakens under the companion matrix-shift package
- chromatogram-level and vendor-execution parity remain outside the current
  proof boundary

## What You Should Not Trust Yet

- vendor-library parity is not earned
- chromatogram-level and vendor-execution parity are not earned
- the current reproduction story still depends on execution steps outside the
  repository proof boundary
- protein-level absence claims stay downgrade-heavy because the second package
  weakens them materially

## Evidence Grounding

- sentence grounding and unsupported-claim review:
  [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
- citation freshness, bibliography export, and gap audits:
  [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/)
