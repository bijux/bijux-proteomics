---
title: LFQ Benchmark Lineage
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# LFQ Benchmark Lineage

The `lfq` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.

## Family Contract

- benchmark title: LFQ cohort review public benchmark package
- public dataset identity: tracked study-scale feature and cohort-design snapshots with explicit missingness and repeatability boundaries
- dataset locator: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- evidence tier: `external_reproduction_package`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
- cross-package generalization report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`

## Raw Source Trail

### primary flagship package

- Study-scale LFQ feature table snapshot copies `packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- checksum: `22e2541ac72bf39edd22f0c67993de86d0929bc7fb30bf0a3093fb3b5e90d0b2`
- public reference: `https://pmc.ncbi.nlm.nih.gov/articles/PMC5862339/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`

### companion generalization package

- Sparse-cohort LFQ feature snapshot copies `packages/bijux-proteomics-core/tests/fixtures/quant/edge_case_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv`
- checksum: `1708c1183e64212dfc5fbe0d25d017683278f0062be49fa4c922b5feb8de92f8`
- public reference: `https://github.com/bijux/bijux-proteomics`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`

## Derived Review Surfaces

- primary package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- primary artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/artifact_inventory.json`
- primary quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/quality_sheet.json`
- companion package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/package_manifest.json`
- companion artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/artifact_inventory.json`
- companion quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/quality_sheet.json`
- family drift report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`

## What This Lineage Does And Does Not Prove

- primary claim scope: Flagship public LFQ cohort review package keeps `lfq` review grounded in `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package` rather than abstract benchmark prose.
- companion claim scope: Companion public LFQ sparse-contrast review package exists to show where `lfq` family transfer weakens, not to hide that drift.
- current cross-package note: This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile.

## Rebuild Order

1. Refresh the primary root with `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`.
2. Refresh the companion root with `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`.
3. Re-read the family drift report before strengthening any workflow-family sentence.
