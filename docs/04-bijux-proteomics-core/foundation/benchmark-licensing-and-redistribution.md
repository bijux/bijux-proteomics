---
title: Benchmark Licensing and Redistribution
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Benchmark Licensing and Redistribution

This page makes the current licensing and redistribution posture explicit for every public benchmark root. It exists so a reviewer can tell the difference between what the repository redistributes as governed evidence and what remains only a public reference or external-engine context.

## Package Matrix

| workflow family | package role | redistributed evidence count | package root |
| --- | --- | --- | --- |
| `dda` | primary flagship package | `5` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run` |
| `dda` | companion generalization package | `7` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package` |
| `dia` | primary flagship package | `5` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package` |
| `dia` | companion generalization package | `4` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package` |
| `lfq` | primary flagship package | `3` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package` |
| `lfq` | companion generalization package | `3` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package` |
| `multiplex` | primary flagship package | `2` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package` |
| `multiplex` | companion generalization package | `2` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package` |
| `ptm` | primary flagship package | `4` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package` |
| `ptm` | companion generalization package | `4` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package` |
| `targeted` | primary flagship package | `4` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package` |
| `targeted` | companion generalization package | `4` | `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package` |

## Licensing Stories

### `dda`: primary flagship package

- package id: `flagship_public_package:dda_reviewable_run`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- dataset reuse note: The tracked DDA package reuses checked-in raw-like and imported-result snapshots as governed benchmark evidence and does not imply redistribution rights for any broader external-engine dataset outside those snapshots.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/spectra.mgf`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/primary/maxquant_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/comparator/msfragger_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/design.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/evidence/workflow_end_to_end_expectations.json`

Current licensing limits:

- The tracked DDA package currently ships checked exported-result snapshots, not live MaxQuant or MSFragger executables.
- The local file is a tracked snapshot; public availability check targets the project source page, not a downloadable binary.
- The local file is a tracked snapshot; public availability check targets the project source page, not an executable redistribution path.
- Public availability check targets the reference resource page used by the package README and citation manifest.

### `dda`: companion generalization package

- package id: `public_companion_package:dda_cross_engine_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
- dataset reuse note: The tracked DDA package reuses checked-in raw-like and imported-result snapshots as governed benchmark evidence and does not imply redistribution rights for any broader external-engine dataset outside those snapshots.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/evidence/spectra.mgf`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/evidence/design.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/evidence/workflow_end_to_end_expectations.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet.params`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/comparator/sage_config.json`

Current licensing limits:

- The DDA companion package ships checked exported-result and raw-like snapshots, not live Comet or Sage executables.
- The local file is a tracked snapshot; the public check targets the project page rather than a binary download.
- The local file is a tracked snapshot; the public check targets the documentation site.

### `dia`: primary flagship package

- package id: `flagship_public_package:dia_library_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- dataset reuse note: The checked-in DIA fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor DIA outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_settings.txt`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_config.json`

Current licensing limits:

- The DIA package currently ships imported report snapshots and settings, not live vendor chromatogram execution.
- The local file is a tracked snapshot; public availability check targets the product reference page.
- The local file is a tracked snapshot; public availability check targets the public project page.

### `dia`: companion generalization package

- package id: `public_companion_package:dia_matrix_shift_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
- dataset reuse note: The checked-in DIA fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor DIA outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/comparator/spectronaut_settings.txt`

Current licensing limits:

- The DIA companion package ships checked exported-result snapshots and remains library-conditioned.
- The local file is a tracked snapshot; the public check targets the project repository.
- The local file is a tracked snapshot; the public check targets the product page.

### `lfq`: primary flagship package

- package id: `flagship_public_package:lfq_cohort_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- dataset reuse note: The checked-in LFQ fixture is reused as internal benchmark evidence and does not widen redistribution rights for any external quantification pipelines beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/quant_reproducibility_manifest.json`

Current licensing limits:

- The LFQ package currently ships cohort-shaped feature and design snapshots, not a second raw cohort or spike-in truth package.
- The local file is a tracked snapshot; public availability check targets the public methodology reference.

### `lfq`: companion generalization package

- package id: `public_companion_package:lfq_sparse_contrast_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
- dataset reuse note: The checked-in LFQ fixture is reused as internal benchmark evidence and does not widen redistribution rights for any external quantification pipelines beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case.design.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/sparse_reproducibility_manifest.json`

Current licensing limits:

- The LFQ companion package ships tracked feature and design snapshots rather than raw vendor data.
- This tracked file is a repository-owned snapshot.

### `multiplex`: primary flagship package

- package id: `flagship_public_package:multiplex_tmtpro_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
- dataset reuse note: The checked-in multiplex fixture is reused as internal benchmark evidence and does not imply redistribution rights for any vendor multiplex outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex.design.tsv`

Current licensing limits:

- The multiplex package currently ships TMTpro-shaped feature and design snapshots, not a raw vendor acquisition replay.
- The local file is a tracked snapshot; public availability check targets the chemistry reference page.

### `multiplex`: companion generalization package

- package id: `public_companion_package:multiplex_channel_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
- dataset reuse note: The checked-in multiplex fixture is reused as internal benchmark evidence and does not imply redistribution rights for any vendor multiplex outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress.design.tsv`

Current licensing limits:

- The multiplex companion package ships a derived stress table rather than raw reporter-ion vendor data.
- This tracked file is a repository-owned derived snapshot.

### `ptm`: primary flagship package

- package id: `flagship_public_package:ptm_localization_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- dataset reuse note: The checked-in PTM fixture is reused as internal benchmark evidence and does not imply redistribution rights beyond the repository’s reviewed test data.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_sites.fasta`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/spectra.mgf`

Current licensing limits:

- The PTM package currently ships localization and occupancy snapshots, not live rescoring or broad PTM-family execution parity.
- The local file is a tracked snapshot; public availability check targets the PTM-localization reference page.

### `ptm`: companion generalization package

- package id: `public_companion_package:ptm_ambiguity_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
- dataset reuse note: The checked-in PTM fixture is reused as internal benchmark evidence and does not imply redistribution rights beyond the repository’s reviewed test data.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/ptm_sites.fasta`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/spectra.mgf`

Current licensing limits:

- The PTM companion package ships tracked ambiguity-stress snapshots rather than vendor-native raw files.
- This tracked file is a repository-owned derived snapshot.

### `targeted`: primary flagship package

- package id: `flagship_public_package:targeted_transition_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- dataset reuse note: The checked-in chromatogram fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor targeted outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/supported_targeted_follow_up.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/failed_targeted_transition_follow_up.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/refused_targeted_follow_up.json`

Current licensing limits:

- The targeted package currently ships transition QC and consequence packet snapshots, not live vendor chromatogram execution or external calibration reruns.
- The local file is a tracked snapshot; public availability check targets the targeted-guideline reference page.

### `targeted`: companion generalization package

- package id: `public_companion_package:targeted_carryover_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
- dataset reuse note: The checked-in chromatogram fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor targeted outputs beyond the repository snapshot.

Redistributed evidence inside the package root:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/supported_targeted_follow_up.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/failed_targeted_transition_follow_up.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/follow_up/refused_targeted_follow_up.json`

Current licensing limits:

- The targeted companion package ships a derived QC table and copied follow-up packets rather than vendor-native chromatograms.
- This tracked file is a repository-owned derived snapshot.
