---
title: Benchmark Asset Audit
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Benchmark Asset Audit

This page re-audits every public benchmark asset root that carries flagship or family-generalization pressure. It keeps the outsider-findable raw source, copied checksum, extraction step, derived review paths, and owning rebuild command visible from one handbook page.

## Coverage

| workflow family | package role | package root | source count | support files present |
| --- | --- | --- | --- | --- |
| `dda` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run` | `3` | yes |
| `dda` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package` | `2` | yes |
| `dia` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package` | `2` | yes |
| `dia` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package` | `2` | yes |
| `lfq` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package` | `1` | yes |
| `lfq` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package` | `1` | yes |
| `multiplex` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package` | `1` | yes |
| `multiplex` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package` | `1` | yes |
| `ptm` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package` | `1` | yes |
| `ptm` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package` | `1` | yes |
| `targeted` | primary flagship package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package` | `1` | yes |
| `targeted` | companion generalization package | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package` | `1` | yes |

## Package Audits

### `dda`: Flagship public DDA reviewable run

- package id: `flagship_public_package:dda_reviewable_run`
- package role: primary flagship package
- benchmark title: DDA reviewable public benchmark package
- public dataset identity: tracked raw-like spectrum plus paired MaxQuant and MSFragger exported-result snapshots inside one outsider-readable DDA package
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| MaxQuant DDA export snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/primary/maxquant_pipeline_export.tsv` | `e4e83e3d45817dded49899f201b5933ac30dfd61355a1246f111549afc82f427` | `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |
| MSFragger comparator export snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/comparator/msfragger_pipeline_export.tsv` | `fb6fbbb6d104dda343db8eb0d084904f246e477661278610346168a7db9c1e24` | `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |
| UniProt reference proteome design context | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/design.tsv` | `59a5f9786b825bca78ab9e046a07de06baf76ba484b6cd3acb3a64b0ba013c0d` | `packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/primary/maxquant_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.
- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/comparator/msfragger_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.
- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/design.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `dda`: Companion public DDA cross-engine review package

- package id: `public_companion_package:dda_cross_engine_review_package`
- package role: companion generalization package
- benchmark title: DDA reviewable public benchmark package
- public dataset identity: tracked Comet primary export plus Sage comparator export with production-run spectrum context and slightly higher sample-complexity pressure
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Comet DDA companion export snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv` | `a6703d9c661db306f31ebe597d84a6af95f1edb4cc693476fc13ad2e85776f8e` | `packages/bijux-proteomics-core/tests/fixtures/search_adapters/comet_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |
| Sage DDA companion comparator snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_pipeline_export.tsv` | `a8d6bdc68faf5287b4084a9ff40dfe0fd4cf4ab9c116aff5a9284051ec6039ce` | `packages/bijux-proteomics-core/tests/fixtures/search_adapters/sage_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapters/comet_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.
- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapters/sage_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `dia`: Flagship public DIA library review package

- package id: `flagship_public_package:dia_library_review_package`
- package role: primary flagship package
- benchmark title: DIA library review public benchmark package
- public dataset identity: tracked Spectronaut-style and DIA-NN-style exported-result snapshots with explicit library-conditioned settings and confrontation scope
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Spectronaut DIA report snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv` | `60b2d626e92541abbd2462a293117af63829cc0c96a41077fa9408dfac3609df` | `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |
| DIA-NN comparator export snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv` | `4d8e06e9ac5f9d57e861c70e47199149d5cdaddf1738bd90026d463672c9a9d6` | `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`, then rerun the package refresh command so the derived metadata stays in sync.
- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `dia`: Companion public DIA matrix-shift review package

- package id: `public_companion_package:dia_matrix_shift_review_package`
- package role: companion generalization package
- benchmark title: DIA library review public benchmark package
- public dataset identity: tracked DIA-NN primary report and pipeline export paired against a Spectronaut comparator with visibly thinner matrix support
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| DIA-NN companion report snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv` | `14e14b95d9cf889f0d2cf847a2fce4666942c51c65ef19d6192a0fd8d09fc3b5` | `packages/bijux-proteomics-core/tests/fixtures/search_adapters/diann_report.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |
| Spectronaut companion comparator snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv` | `fa4407b18e7c004a0c96fb0e72544c0c142007acc4fcdb4ccb13bf201e4b6068` | `packages/bijux-proteomics-core/tests/fixtures/search_adapters/spectronaut_pipeline_export.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapters/diann_report.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv`, then rerun the package refresh command so the derived metadata stays in sync.
- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/search_adapters/spectronaut_pipeline_export.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `lfq`: Flagship public LFQ cohort review package

- package id: `flagship_public_package:lfq_cohort_review_package`
- package role: primary flagship package
- benchmark title: LFQ cohort review public benchmark package
- public dataset identity: tracked study-scale feature and cohort-design snapshots with explicit missingness and repeatability boundaries
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Study-scale LFQ feature table snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv` | `22e2541ac72bf39edd22f0c67993de86d0929bc7fb30bf0a3093fb3b5e90d0b2` | `packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `lfq`: Companion public LFQ sparse-contrast review package

- package id: `public_companion_package:lfq_sparse_contrast_review_package`
- package role: companion generalization package
- benchmark title: LFQ cohort review public benchmark package
- public dataset identity: tracked sparse-cohort feature and design snapshots with a different replicate shape and more fragile biological contrast
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Sparse-cohort LFQ feature snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv` | `1708c1183e64212dfc5fbe0d25d017683278f0062be49fa4c922b5feb8de92f8` | `packages/bijux-proteomics-core/tests/fixtures/quant/edge_case_ms1_features.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/quant/edge_case_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `multiplex`: Flagship public multiplex TMTpro review package

- package id: `flagship_public_package:multiplex_tmtpro_review_package`
- package role: primary flagship package
- benchmark title: Multiplex TMTpro public benchmark package
- public dataset identity: tracked TMTpro feature and design snapshots with explicit reporter-channel, imbalance, and missing-channel pressure
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| TMTpro multiplex feature table snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv` | `54ef1f14ff94f9bbfdb4430e940b641ac3d6c31e13d3f71c8566c5dd1b63f48b` | `packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `multiplex`: Companion public multiplex channel-stress review package

- package id: `public_companion_package:multiplex_channel_stress_review_package`
- package role: companion generalization package
- benchmark title: Multiplex TMTpro public benchmark package
- public dataset identity: tracked multiplex feature and design snapshots with stronger pooled-reference dominance and missing-channel pressure
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Channel-stress multiplex feature snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv` | `90ae2afd5143403218c04d40c8976c3ffa2fefa0833ea99c65cff7bdf7d1271c` | `packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `ptm`: Flagship public PTM localization review package

- package id: `flagship_public_package:ptm_localization_review_package`
- package role: primary flagship package
- benchmark title: PTM localization public benchmark package
- public dataset identity: tracked localization, PTM feature, raw-spectrum, and sequence-context snapshots with explicit ambiguity limits
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| PTM localization result snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv` | `a711e01b793af64df1c24802a661a53eb8c88a7d5abee2b66cd7fab89cc054d1` | `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `ptm`: Companion public PTM ambiguity-stress review package

- package id: `public_companion_package:ptm_ambiguity_stress_review_package`
- package role: companion generalization package
- benchmark title: PTM localization public benchmark package
- public dataset identity: tracked PTM localization evidence with materially worse ambiguity and lower localization confidence than the flagship package
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| PTM ambiguity-stress localization snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv` | `f85243b0a4a3332e52671a60ce6f397202d9aa7ec1f15a6abf57a436a55d2150` | `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `targeted`: Flagship public targeted transition review package

- package id: `flagship_public_package:targeted_transition_review_package`
- package role: primary flagship package
- benchmark title: Targeted transition public benchmark package
- public dataset identity: tracked chromatogram-shaped QC table plus approved, failed, and refused follow-up packet snapshots
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Targeted QC evidence snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv` | `6a723089259103a443ca23360c62d49d9acacda1e2e266244a8cf4d1ca509418` | `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.flagship_asset_maintenance refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.

### `targeted`: Companion public targeted carryover review package

- package id: `public_companion_package:targeted_carryover_review_package`
- package role: companion generalization package
- benchmark title: Targeted transition public benchmark package
- public dataset identity: tracked targeted QC and follow-up evidence with stronger carryover drift and heavier refusal pressure than the flagship package
- evidence tier: `external_reproduction_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/source_locator_manifest.json`
- citation manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/citation_manifest.json`
- generated boundary manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/generated_boundary.json`
- rebuild instructions: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/rebuild_instructions.md`
- derived package manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/package_manifest.json`
- derived artifact inventory: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/artifact_inventory.json`
- derived quality sheet: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/quality_sheet.json`
- derived lifecycle record: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/lifecycle.json`

| source name | copied path | sha256 | tracked upstream source | rebuild command |
| --- | --- | --- | --- | --- |
| Targeted carryover QC snapshot | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv` | `fafc32570937de937657c9ffb00545950824aca43512d767fa3c1ca29b007eb8` | `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` | `uv run --group dev python -m bijux_proteomics.benchmarks.workflow_generalization_assets refresh` |

Copied-source extraction discipline:

- Copy the tracked snapshot from `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv` into `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv`, then rerun the package refresh command so the derived metadata stays in sync.

The audit keeps raw source, checksum, extraction step, derived review paths, and the owning rebuild command visible without leaving the repository.
