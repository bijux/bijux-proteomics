---
title: Benchmark Rerun Kits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Benchmark Rerun Kits

These rerun kits are the shortest path through the shipped package roots and runtime entrypoints for each workflow family. Each kit names the primary package, the companion package, the exact runtime entrypoints, and the review surfaces that still keep the family bounded.

Use this page when the reader already accepts the family-level trust sentence
and now wants the exact reopen order. The goal is not to describe every
artifact in the repository. The goal is to get an independent reviewer from
the released package root to the strongest checked rerun lane without
maintainer narration.

## How To Use A Kit

- open the primary package root first because that is the public release anchor
- open the companion package second because it shows whether the family still
  holds under a harder adjacent lane
- open the runtime entrypoint and validating tests before claiming that the
  shipped rerun route is executable
- treat the remaining limits as part of the kit, not as optional caveats

## What A Good Rerun Kit Gives A Reviewer

- one public root to start from
- one companion route that tests whether the family still holds under stress
- one explicit runtime entrypoint instead of folklore about which script counts
- one visible list of remaining limits so the rerun lane is not oversold

## `dda`

- public release language: `outsider_auditable_bounded`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path`
- primary run mode: `import_only`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dda_generalization_import_path`
- companion run mode: `import_only`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/artifact_inventory.json`
- `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/primary/comet_pipeline_export.tsv`
- `artifacts/intelligence/independent-reruns/dda_independent_rerun_dossier.json`
- `artifacts/intelligence/external-review-kits/dda_external_review_kit.json`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `artifacts/intelligence/independent-reruns/dda_independent_rerun_dossier.json`
- external review kit: `artifacts/intelligence/external-review-kits/dda_external_review_kit.json`

Remaining limits:

- no in-repo live-engine rerun parity
- one-run package cannot authorize broad production-cohort DDA claims
- no live-engine rerun parity
- generalization remains bounded to two small exported-result packages
- The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.
- The strongest shipped rerun lane is still import-backed rather than a raw external-engine execution owned by this repository.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.

## `dia`

- public release language: `outsider_auditable_bounded`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_review_path`
- primary run mode: `raw_executable`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_generalization_review_path`
- companion run mode: `raw_executable`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/primary/diann_report.tsv`
- `artifacts/intelligence/independent-reruns/dia_independent_rerun_dossier.json`
- `artifacts/intelligence/external-review-kits/dia_external_review_kit.json`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `artifacts/intelligence/independent-reruns/dia_independent_rerun_dossier.json`
- external review kit: `artifacts/intelligence/external-review-kits/dia_external_review_kit.json`

Remaining limits:

- no chromatogram-level vendor parity
- library incompleteness and absent-peptide consequences still block broader biological confidence
- protein-evidence transfer remains weaker than precursor-level review transfer
- library-conditioned authority still caps the family posture
- The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.
- The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.

## `lfq`

- public release language: `outsider_auditable_bounded`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_review_path`
- primary run mode: `raw_executable`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_generalization_review_path`
- companion run mode: `raw_executable`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/evidence/edge_case_ms1_features.tsv`
- `artifacts/intelligence/independent-reruns/lfq_independent_rerun_dossier.json`
- `artifacts/intelligence/external-review-kits/lfq_external_review_kit.json`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `artifacts/intelligence/independent-reruns/lfq_independent_rerun_dossier.json`
- external review kit: `artifacts/intelligence/external-review-kits/lfq_external_review_kit.json`

Remaining limits:

- no stronger public truth package for accuracy beyond repeatability
- generalization beyond the current cohort package remains explicitly bounded
- effect-direction confidence weakens under sparser contrast
- family authority remains bounded rather than decision-grade
- The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.
- The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.

## `multiplex`

- public release language: `internal_support_only`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_review_path`
- primary run mode: `raw_executable`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_generalization_review_path`
- companion run mode: `raw_executable`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/evidence/multiplex_channel_stress_ms1_features.tsv`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `not published for this family`
- external review kit: `not published for this family`

Remaining limits:

- no multiplex lab packet or outsider decision brief family
- multiplex authority is intentionally kept out of the outsider-facing flagship set
- multiplex still lacks outsider review and lab consequence posture
- public release language remains internal-support only even with a second package
- Multiplex remains internal-support only, so the rerun kit is reviewable but not a route to outsider-auditable language.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.

## `ptm`

- public release language: `outsider_auditable_bounded`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_review_path`
- primary run mode: `raw_executable`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_generalization_review_path`
- companion run mode: `raw_executable`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/evidence/localization_results.tsv`
- `artifacts/intelligence/independent-reruns/ptm_independent_rerun_dossier.json`
- `artifacts/intelligence/external-review-kits/ptm_external_review_kit.json`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `artifacts/intelligence/independent-reruns/ptm_independent_rerun_dossier.json`
- external review kit: `artifacts/intelligence/external-review-kits/ptm_external_review_kit.json`

Remaining limits:

- occupancy and regulatory interpretation still remain narrower than localization evidence
- PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning
- targetability weakens materially under ambiguity stress
- family authority remains bounded rather than decision-grade
- The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.
- The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.

## `targeted`

- public release language: `outsider_auditable_bounded`
- primary package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- companion package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
- primary runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_review_path`
- primary run mode: `raw_executable`
- companion runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_generalization_review_path`
- companion run mode: `raw_executable`

Opening order:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/evidence/targeted_benchmark_qc.tsv`
- `artifacts/intelligence/independent-reruns/targeted_independent_rerun_dossier.json`
- `artifacts/intelligence/external-review-kits/targeted_external_review_kit.json`

Validating tests:

- `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`

- independent rerun dossier: `artifacts/intelligence/independent-reruns/targeted_independent_rerun_dossier.json`
- external review kit: `artifacts/intelligence/external-review-kits/targeted_external_review_kit.json`

Remaining limits:

- vendor-parity and calibration-clean authority are still outside the current proof boundary
- targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty
- stronger carryover pressure weakens promotion confidence
- family authority remains bounded by calibration and vendor-parity limits
- The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary.
- The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions.

Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration.
