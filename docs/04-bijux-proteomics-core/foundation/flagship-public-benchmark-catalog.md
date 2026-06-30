---
title: Flagship Public Benchmark Catalog
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-07
---

# Flagship Public Benchmark Catalog

`bijux-proteomics-core` now publishes one explicit catalog for the flagship
public benchmark packages and their companion generalization packages that
downstream review, runtime, knowledge, and lab surfaces rely on.

The point of this catalog is not volume. It is to make one reviewer ask and one
answer possible:

Which public packages exist for this workflow family, what exact artifacts do
they expose, and what authority still stays blocked when the family is forced
off its easiest package?

## Current Catalog

- `dda`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, scientific invariants, warning demonstrations
- `dia`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, Spectronaut-style report, Spectronaut-style
    pipeline export, DIA-NN-style pipeline export
- `lfq`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, study-scale feature table, cohort design table
- `multiplex`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, reporter feature table, multiplex design table
- `ptm`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, localization table, PTM feature table, reference
    FASTA, raw spectra
- `targeted`
  - flagship package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
  - companion package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
  - family-transfer report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/cross_package_generalization.json`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, targeted QC table, approved follow-up packet,
    failed follow-up packet, refused follow-up packet

## What This Catalog Guarantees

- every flagship family has one durable package root instead of scattered proof
  fragments
- every flagship family also has one companion package and one published
  family-transfer report before family-level trust language is allowed
- every package ships machine-readable package identity, artifact inventory,
  quality posture, and lifecycle posture
- every package also ships a source locator manifest, citation manifest,
  generated-boundary manifest, and rebuild instructions
- every downstream surface can point to one concrete paired-package evidence set
  instead of describing a benchmark family abstractly

## What This Catalog Does Not Guarantee

- outsider-auditable authority for every workflow family
- live runtime execution for every package
- comparator parity for every package
- decision-grade scientific support across the whole catalog
- stability across more than the current two-package family pair for each
  workflow family

`multiplex` stays an internal-support family even though it already has a real
pair of public packages and a raw-executable runtime lane, because its
family-transfer report still collapses outsider-facing trust.

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_public_packages.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_asset_roots.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_public_package_surface.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_asset_root_surface.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_workflow_generalization_surface.py`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages`

## Asset Maintenance

Open [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
when you need the copied-source contract, citation discipline, refresh command,
freshness report, or obsolescence audit for these package roots.

Open [Flagship Challenge Corpus Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-challenge-corpus-catalog/)
when you need the blinded holdouts and perturbation roots that deliberately try
to break the claims these package roots would otherwise make too comfortably.

## Next Routes

- Open [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when the question becomes which family currently deserves stronger public
  language.
- Open [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  when the question becomes how these package roots turn into rerun lanes and
  checked runtime artifacts.
- Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question becomes whether grounding, recommendation posture, or
  release language outruns the package story.
