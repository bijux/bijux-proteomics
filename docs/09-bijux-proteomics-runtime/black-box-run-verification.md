---
title: Black-Box Run Verification
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Black-Box Run Verification

These routes begin from one public benchmark asset and end at one checked runtime bundle, stage lineage artifact, and replay challenge. The route is black-box on purpose: the reader should not need maintainer narration to find the next artifact.

This page is narrower than the rerun kits. The rerun kits answer "where do I
start for this family?" This page answers "what exact artifact chain proves
that the shipped benchmark packet became the checked runtime story?"

## What Counts As Verification

- the benchmark entry artifact fixes the public package boundary
- the source locator manifest proves where the benchmark packet points for its
  runtime-facing inputs
- the checked runtime bundle proves the emitted execution summary that the
  repository currently stands behind
- the stage lineage artifact shows that the run is not only a terminal output
- the replay artifact shows how the same route should fail under hostile
  pressure rather than only how it succeeds

## `dda`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/source_locator_manifest.json`
- runtime package id: `dda-maxquant-pipeline-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path`
- run mode: `import_only`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## `dia`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/source_locator_manifest.json`
- runtime package id: `dia-diann-pipeline-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_dia_review_path`
- run mode: `raw_executable`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## `lfq`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/source_locator_manifest.json`
- runtime package id: `lfq-cohort-review-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_lfq_review_path`
- run mode: `raw_executable`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## `multiplex`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/source_locator_manifest.json`
- runtime package id: `multiplex-tmtpro-review-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_multiplex_review_path`
- run mode: `raw_executable`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## `ptm`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/source_locator_manifest.json`
- runtime package id: `ptm-localization-review-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_ptm_review_path`
- run mode: `raw_executable`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## `targeted`

- benchmark entry artifact: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
- source locator manifest: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/source_locator_manifest.json`
- runtime package id: `targeted-transition-review-corpus`
- runtime entrypoint: `bijux_proteomics_runtime.workflows.benchmark_runs.run_benchmark_targeted_review_path`
- run mode: `raw_executable`
- checked runtime bundle: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`
- stage lineage artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/stage_lineage.json`
- replay artifact: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`
- validating tests: `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`
- note: Open the public benchmark manifest first, then the source locator, then the checked runtime bundle, stage lineage, and replay artifact. The route is meant to survive without maintainer narration.

## What This Route Protects Against

- claiming that a benchmark package is reviewable when no checked runtime story
  exists
- confusing a successful bundle with an untested replay boundary
- hiding execution lineage behind one terminal artifact
