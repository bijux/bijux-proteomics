---
title: Runtime Artifact Stability
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-09
---

# Runtime Artifact Stability

This page states what must remain bit-stable, value-stable, or review-stable across repeated flagship reruns. It also names the environment-bound drift that is allowed without pretending the rerun changed meaningfully.

## `dda`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- value-stable surfaces: runtime package id `dda-maxquant-pipeline-corpus`, run mode `import_only`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.

## `dia`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- value-stable surfaces: runtime package id `dia-diann-pipeline-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.

## `lfq`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- value-stable surfaces: runtime package id `lfq-cohort-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.

## `multiplex`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- value-stable surfaces: runtime package id `multiplex-tmtpro-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.

## `ptm`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- value-stable surfaces: runtime package id `ptm-localization-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.

## `targeted`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`
- value-stable surfaces: runtime package id `targeted-transition-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`
- note: Bit-stable paths are checked fixture artifacts. Value-stable and review-stable surfaces may change wording only when the underlying runtime or scientific boundary changes in the same reviewable edit.
