---
title: Targeted Benchmark Lineage
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Targeted Benchmark Lineage

The `targeted` family now has a two-root lineage instead of one convenient package story. This page ties the primary flagship package, the companion generalization package, and the cross-package drift report together so an outsider can follow the evidence chain from copied input to derived review surface.

## Family Contract

- benchmark title: Targeted transition public benchmark package
- public dataset identity: tracked chromatogram-shaped QC table plus approved, failed, and refused follow-up packet snapshots
- dataset locator: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
- evidence tier: `external_reproduction_package`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
- cross-package generalization report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/cross_package_generalization.json`

## Raw Source Trail

### primary flagship package

- Targeted QC evidence snapshot copies `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`
- checksum: `6a723089259103a443ca23360c62d49d9acacda1e2e266244a8cf4d1ca509418`
- public reference: `https://pubmed.ncbi.nlm.nih.gov/21423193/`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`

### companion generalization package

- Targeted carryover QC snapshot copies `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv`
- checksum: `fafc32570937de937657c9ffb00545950824aca43512d767fa3c1ca29b007eb8`
- public reference: `https://github.com/bijux/bijux-proteomics`
- rebuild command: `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`

## Derived Review Surfaces

- primary package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
- primary artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/artifact_inventory.json`
- primary quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/quality_sheet.json`
- companion package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/package_manifest.json`
- companion artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/artifact_inventory.json`
- companion quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/quality_sheet.json`
- family drift report: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/cross_package_generalization.json`

## What This Lineage Does And Does Not Prove

- primary claim scope: Flagship public targeted transition review package keeps `targeted` review grounded in `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package` rather than abstract benchmark prose.
- companion claim scope: Companion public targeted carryover review package exists to show where `targeted` family transfer weakens, not to hide that drift.
- current cross-package note: This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile.

## Rebuild Order

1. Refresh the primary root with `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh`.
2. Refresh the companion root with `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh`.
3. Re-read the family drift report before strengthening any workflow-family sentence.
