---
title: Runtime Replay Challenges
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Runtime Replay Challenges

Each challenge starts from a clean environment, reopens the tracked benchmark package, and asks the smallest hostile question that should still reconstruct the shipped runtime artifact story.

These are not full benchmark reruns and they are not broad scientific
acceptance suites. They are disciplined replay pressure. Each challenge asks
whether the runtime lane can re-emit the checked story and whether the failure
surface stays visible when the lane is stressed.

## What A Successful Replay Proves

- the reviewer can reopen the shipped public package without hidden local state
- the runtime lane still reconstructs the checked bundle and lineage artifacts
- invalidation is documented as part of the route rather than treated as an
  embarrassing exception
- the family still stops exactly where the current release language says it
  stops

## `dda`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- do not substitute a live external engine; the current faithful rerun path is the shipped imported-result lane

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path` against `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_import`
- current limit: dda replay is real for the shipped imported-result lane, but it still refuses broader raw-engine rerun claims.

## `dia`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_review_path` against `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_input`
- current limit: DIA replay is real for the shipped runtime lane, but it still refuses chromatogram-native and broader vendor-parity claims.

## `lfq`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_review_path` against `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_input`
- current limit: lfq replay is real for the shipped runtime lane, but it still inherits the same benchmark and downstream claim limits as the checked bundle.

## `multiplex`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_review_path` against `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_input`
- current limit: multiplex replay is real for the shipped runtime lane, but it still inherits the same benchmark and downstream claim limits as the checked bundle.

## `ptm`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_review_path` against `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_input`
- current limit: ptm replay is real for the shipped runtime lane, but it still inherits the same benchmark and downstream claim limits as the checked bundle.

## `targeted`

Clean-environment requirements:

- start from a clean working directory with no prior runtime artifacts
- use Python 3.11 and the repository-managed uv environment
- open the tracked benchmark package rooted at `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`

Minimal steps:

- open `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json` to confirm the public benchmark package boundary
- run `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_review_path` against `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv`
- compare the emitted runtime bundle to `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`
- challenge invalidation with `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`

- expected artifacts: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`
- invalidation cases: `execution_failure`, `scientific_invalidation`, `structurally_incomplete_input`
- current limit: targeted replay is real for the shipped runtime lane, but it still inherits the same benchmark and downstream claim limits as the checked bundle.

## Reading Discipline

- use the clean-environment requirements to avoid false confidence from a dirty
  local workspace
- treat the invalidation cases as part of the proof surface because a replay
  route that only describes success is incomplete
- hand off to environment contracts and artifact stability when the reviewer
  asks whether the same replay should remain stable across repeated runs
