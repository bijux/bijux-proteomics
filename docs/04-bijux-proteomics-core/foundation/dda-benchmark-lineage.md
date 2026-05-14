---
title: DDA Benchmark Lineage
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# DDA Benchmark Lineage

The `dda` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.

## Family Contract

- benchmark title: DDA reviewable public benchmark package
- public dataset identity: tracked raw-like spectrum plus paired MaxQuant and MSFragger exported-result snapshots inside one outsider-readable DDA package
- dataset locator: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- evidence tier: `external_reproduction_package`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
- cross-package generalization report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`

## Raw Source Trail

### primary flagship package

- MaxQuant DDA export snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/primary/maxquant_pipeline_export.tsv`
- checksum: `e4e83e3d45817dded49899f201b5933ac30dfd61355a1246f111549afc82f427`
- public reference: `https://www.maxquant.org/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`
- MSFragger comparator export snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/comparator/msfragger_pipeline_export.tsv`
- checksum: `fb6fbbb6d104dda343db8eb0d084904f246e477661278610346168a7db9c1e24`
- public reference: `https://msfragger.nesvilab.org/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`
- UniProt reference proteome design context copies `packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/design.tsv`
- checksum: `59a5f9786b825bca78ab9e046a07de06baf76ba484b6cd3acb3a64b0ba013c0d`
- public reference: `https://www.uniprot.org`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`

### companion generalization package

- Comet DDA companion export snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapters/comet_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv`
- checksum: `a6703d9c661db306f31ebe597d84a6af95f1edb4cc693476fc13ad2e85776f8e`
- public reference: `https://uwpr.github.io/Comet/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`
- Sage DDA companion comparator snapshot copies `packages/bijux-proteomics-core/tests/fixtures/search_adapters/sage_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_pipeline_export.tsv`
- checksum: `a8d6bdc68faf5287b4084a9ff40dfe0fd4cf4ab9c116aff5a9284051ec6039ce`
- public reference: `https://sage-docs.vercel.app/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`

## Derived Review Surfaces

- primary package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- primary artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/artifact_inventory.json`
- primary quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/quality_sheet.json`
- companion package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/package_manifest.json`
- companion artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/artifact_inventory.json`
- companion quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/quality_sheet.json`
- family drift report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`

## What This Lineage Does And Does Not Prove

- primary claim scope: Flagship public DDA reviewable run keeps `dda` review grounded in `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run` rather than abstract benchmark prose.
- companion claim scope: Companion public DDA cross-engine review package exists to show where `dda` family transfer weakens, not to hide that drift.
- current cross-package note: This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile.

## Rebuild Order

1. Refresh the primary root with `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`.
2. Refresh the companion root with `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`.
3. Re-read the family drift report before strengthening any workflow-family sentence.
