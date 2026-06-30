---
title: Raw Versus Import Execution
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-09
---

# Raw Versus Import Execution

This page makes the execution-mode boundary explicit for each flagship workflow family. It exists to stop import-backed or library-conditioned lanes from quietly inheriting stronger raw-rerun language.

## Why This Distinction Matters

- execution mode is one of the easiest places for docs to overstate what the
  repository really proves
- a lane can be useful, reviewable, and still not deserve raw-native or
  vendor-parity language
- this page keeps runtime honesty separate from benchmark strength and downstream
  recommendation strength

| workflow family | current run mode | raw rerun supported | imported dependency count |
| --- | --- | --- | --- |
| `dda` | `import_only` | no | `3` |
| `dia` | `raw_executable` | yes | `5` |
| `lfq` | `raw_executable` | yes | `3` |
| `multiplex` | `raw_executable` | yes | `2` |
| `ptm` | `raw_executable` | yes | `2` |
| `targeted` | `raw_executable` | yes | `4` |

## Family Boundaries

### `dda`

- mode difference: dda currently reruns through imported exported-result evidence instead of a raw in-repository execution lane.
- imported dependencies: `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv`, `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv`, `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt`
- blocked claims: raw external-engine parity, vendor-native or engine-native reproducibility
- claim guard: dda must not be described as raw-executable while `dda-maxquant-pipeline-corpus` still runs in `import_only` mode.

### `dia`

- mode difference: dia executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity.
- imported dependencies: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_pipeline_export.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_settings.txt`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_pipeline_export.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/comparator/diann_config.json`
- blocked claims: chromatogram-native DIA authority, broad vendor-parity DIA replay
- claim guard: DIA remains raw-executable in runtime terms, but the shipped package still stops short of chromatogram-native and vendor-parity claims.

### `lfq`

- mode difference: lfq executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity.
- imported dependencies: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/quant_reproducibility_manifest.json`
- blocked claims: none
- claim guard: lfq should keep its stronger sentence behind the current benchmark package and downstream consequence limits.

### `multiplex`

- mode difference: multiplex executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity.
- imported dependencies: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex.design.tsv`
- blocked claims: outsider-auditable multiplex trust
- claim guard: Multiplex may rerun in runtime terms while still failing the stronger outsider-facing claim boundary.

### `ptm`

- mode difference: ptm executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity.
- imported dependencies: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/ptm_features.tsv`
- blocked claims: none
- claim guard: ptm should keep its stronger sentence behind the current benchmark package and downstream consequence limits.

### `targeted`

- mode difference: targeted executes inside the runtime package, but its benchmark package can still include imported or derived evidence that does not prove vendor-native parity.
- imported dependencies: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/supported_targeted_follow_up.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/failed_targeted_transition_follow_up.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/follow_up/refused_targeted_follow_up.json`
- blocked claims: none
- claim guard: targeted should keep its stronger sentence behind the current benchmark package and downstream consequence limits.

## What `raw_executable` Still Does Not Mean

- it does not mean vendor-parity authority by itself
- it does not mean companion-package transfer pressure disappeared
- it does not mean downstream lab consequence is already justified
