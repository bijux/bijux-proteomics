---
title: Runtime Artifact Stability
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-21
---

# Runtime Artifact Stability

Artifact stability separates exact bytes, semantic values, reviewer interpretation, and permitted environment metadata. Treating all drift alike would either reject harmless run identity changes or conceal meaningful contract movement.

| stability class | required invariant |
| --- | --- |
| bit stable | governed fixture bytes remain identical |
| value stable | named semantic values retain the same meaning |
| review stable | authorized claim scope and interpretation remain unchanged |
| permitted environment drift | named execution metadata may vary without changing the proof surface |

```mermaid
flowchart LR
    R["repeated run"] --> B["byte comparison"]
    R --> V["semantic value comparison"]
    R --> Q["review interpretation"]
    R --> E["environment metadata"]
    E --> P["allow only declared drift"]
```

## Family Stability Contracts

### `dda`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- value-stable surfaces: runtime package id `dda-maxquant-pipeline-corpus`, run mode `import_only`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

### `dia`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- value-stable surfaces: runtime package id `dia-diann-pipeline-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

### `lfq`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- value-stable surfaces: runtime package id `lfq-cohort-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

### `multiplex`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- value-stable surfaces: runtime package id `multiplex-tmtpro-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

### `ptm`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- value-stable surfaces: runtime package id `ptm-localization-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

### `targeted`

- bit-stable paths: `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/stage_lineage.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`
- value-stable surfaces: runtime package id `targeted-transition-review-corpus`, run mode `raw_executable`, remaining blockers `none`
- review-stable surfaces: authorized claim scope in the runtime bundle, family-specific replay invalidation reasons, downstream owner links carried by the checked runtime bundle
- permitted environment drift: `run_id`, `environment.environment_id`, `run_summary.artifacts_dir`

## Change Rule

A bit-stable path changes only through an intentional governed fixture update.
Value-stable or review-stable surfaces change only when the underlying runtime
or scientific boundary changes in the same reviewable edit. Permitted
environment drift never authorizes a claim, blocker, or lineage change.

Stable execution protects rerun honesty; it does not enlarge biological,
analytical, vendor-parity, recommendation, or lab authority.
