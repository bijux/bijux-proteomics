---
title: PTM Benchmark Lineage
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# PTM Benchmark Lineage

The `ptm` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.

## Family Contract

- benchmark title: PTM localization public benchmark package
- public dataset identity: tracked localization, PTM feature, raw-spectrum, and sequence-context snapshots with explicit ambiguity limits
- dataset locator: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`
- evidence tier: `external_reproduction_package`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
- cross-package generalization report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/cross_package_generalization.json`

## Raw Source Trail

### primary flagship package

- PTM localization result snapshot copies `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`
- checksum: `a711e01b793af64df1c24802a661a53eb8c88a7d5abee2b66cd7fab89cc054d1`
- public reference: `https://pubmed.ncbi.nlm.nih.gov/16964243/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`

### companion generalization package

- PTM ambiguity-stress localization snapshot copies `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv`
- checksum: `f85243b0a4a3332e52671a60ce6f397202d9aa7ec1f15a6abf57a436a55d2150`
- public reference: `https://github.com/bijux/bijux-proteomics`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`

## Derived Review Surfaces

- primary package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`
- primary artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/artifact_inventory.json`
- primary quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/quality_sheet.json`
- companion package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/package_manifest.json`
- companion artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/artifact_inventory.json`
- companion quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/quality_sheet.json`
- family drift report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/cross_package_generalization.json`

## What This Lineage Does And Does Not Prove

- primary claim scope: Flagship public PTM localization review package keeps `ptm` review grounded in `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package` rather than abstract benchmark prose.
- companion claim scope: Companion public PTM ambiguity-stress review package exists to show where `ptm` family transfer weakens, not to hide that drift.
- current cross-package note: This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile.

## Rebuild Order

1. Refresh the primary root with `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`.
2. Refresh the companion root with `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`.
3. Re-read the family drift report before strengthening any workflow-family sentence.
