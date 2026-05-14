---
title: DIA Benchmark Lineage
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# DIA Benchmark Lineage

The `dia` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.

## Family Contract

- benchmark title: DIA library review public benchmark package
- public dataset identity: tracked Spectronaut-style and DIA-NN-style exported-result snapshots with explicit library-conditioned settings and confrontation scope
- dataset locator: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- evidence tier: `external_reproduction_package`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
- cross-package generalization report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`

## Raw Source Trail

### primary flagship package

- Spectronaut DIA report snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`
- checksum: `60b2d626e92541abbd2462a293117af63829cc0c96a41077fa9408dfac3609df`
- public reference: `https://biognosys.com/software/spectronaut/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`
- DIA-NN comparator export snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv`
- checksum: `4d8e06e9ac5f9d57e861c70e47199149d5cdaddf1738bd90026d463672c9a9d6`
- public reference: `https://github.com/vdemichev/DiaNN`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`

### companion generalization package

- DIA-NN companion report snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapters/diann_report.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv`
- checksum: `14e14b95d9cf889f0d2cf847a2fce4666942c51c65ef19d6192a0fd8d09fc3b5`
- public reference: `https://github.com/vdemichev/DiaNN`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`
- Spectronaut companion comparator snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapters/spectronaut_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv`
- checksum: `fa4407b18e7c004a0c96fb0e72544c0c142007acc4fcdb4ccb13bf201e4b6068`
- public reference: `https://biognosys.com/software/spectronaut/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`

## Derived Review Surfaces

- primary package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- primary artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/artifact_inventory.json`
- primary quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/quality_sheet.json`
- companion package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/package_manifest.json`
- companion artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/artifact_inventory.json`
- companion quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/quality_sheet.json`
- family drift report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`

## What This Lineage Does And Does Not Prove

- primary claim scope: Flagship public DIA library review package keeps `dia` review grounded in `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package` rather than abstract benchmark prose.
- companion claim scope: Companion public DIA matrix-shift review package exists to show where `dia` family transfer weakens, not to hide that drift.
- current cross-package note: This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile.

## Rebuild Order

1. Refresh the primary root with `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`.
2. Refresh the companion root with `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`.
3. Re-read the family drift report before strengthening any workflow-family sentence.
