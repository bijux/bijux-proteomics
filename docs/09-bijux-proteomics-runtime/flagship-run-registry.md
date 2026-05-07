---
title: Flagship Run Registry
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-07
---

# Flagship Run Registry

This page names the runtime-owned flagship public runs that are actually checked
in today. It is the runtime answer to a simple question:

Which public benchmark runs can I open right now, and what do they really
authorize?

## Open The Checked Artifacts

- `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/runtime_run_registry.json`
- `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/cross_family_run_bundle.json`

Per-family artifacts:

- `dda`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- `dia`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- `lfq`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- `multiplex`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- `ptm`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- `targeted`:
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/stage_lineage.json`
  - `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`

## Current Runtime Families

| Workflow | Runtime package id | Current lane |
| --- | --- | --- |
| `dda` | `dda-maxquant-pipeline-corpus` | strict import lane over tracked MaxQuant exports |
| `dia` | `dia-diann-pipeline-corpus` | strict import lane over tracked DIA-NN exports |
| `lfq` | `lfq-cohort-review-corpus` | raw-executable review lane over tracked feature and design tables |
| `multiplex` | `multiplex-tmtpro-review-corpus` | raw-executable review lane over tracked channel feature and design tables |
| `ptm` | `ptm-localization-review-corpus` | raw-executable review lane over tracked localization, feature, and FASTA evidence |
| `targeted` | `targeted-transition-review-corpus` | strict import-facing review lane over tracked QC and follow-up artifacts |

## What These Bundles Authorize

- they authorize exactly the claim scopes listed in each `run_bundle.json`
- they do not erase comparator refusal, thin grounding, or unjustified lab
  burden downstream
- they keep the runtime stage lineage and failure replay story public instead of
  forcing readers to trust runtime prose

## Boundary

These bundles prove runtime execution and runtime traceability. They do not
automatically upgrade knowledge, comparator, recommendation, or lab authority.
Use the cross-family bundle to see those downstream owners directly.
