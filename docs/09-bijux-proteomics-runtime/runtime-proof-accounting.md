---
title: Runtime Proof Accounting
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-07
---

# Runtime Proof Accounting

Runtime now names exactly what kind of proof each shipped claim uses. That is
the difference between a real execution product and a tidy fiction.

## Proof Classes

- `raw_execution`: the workflow ran through a real runtime path over tracked
  inputs and produced reviewable runtime artifacts.
- `import_backed_execution`: the runtime lane is real, but the strongest
  current proof still starts from imported external-engine results rather than
  raw execution inside the repository.
- `replay_backed_execution`: the claim is about replay, invalidation, or
  recovery behavior over a real runtime lane.
- `simulation_only`: the surface is intentionally a simulation contract and is
  excluded from flagship proof accounting.

## Current Flagship Runtime Boundary

Current strongest flagship runtime classes:

- `sequence_to_digest`: `raw_execution`
- `dda_import`: `import_backed_execution`
- `dia_import`: `import_backed_execution`
- `quant_review`: `raw_execution`
- `multiplex_review`: `raw_execution`
- `ptm_review`: `raw_execution`
- `targeted_review`: `import_backed_execution`

The current simulation-only exceptions are explicit and narrow:

- `packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py`
- `packages/bijux-proteomics-runtime/tests/api/test_runtime_cli_surface.py`
- `packages/bijux-proteomics-runtime/tests/performance/test_runtime_execution_control_benchmark_surface.py`

Those tests are allowed to use fake helpers only because they are excluded from
flagship proof accounting. If a fake helper appears inside a runtime family
used for end-to-end, integrity, replay, or flagship execution authority, the
runtime proof gate must block release-facing trust.

## Promotion Checklist

Before promoting a workflow family from `simulation_only` or
`import_backed_execution` to `raw_execution`, maintainers must close the path
named for that family instead of broadening trust by prose:

- `dda_import`:
  - `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
  - replace `run_benchmark_dda_import_path` with one raw review path over
    tracked DDA spectra-side inputs
- `dia_import`:
  - `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
  - replace `run_benchmark_dia_import_path` with one raw review path over
    tracked DIA acquisition-side inputs
- `targeted_review`:
  - `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`
  - add tracked acquisition-side evidence and promote the runtime lane beyond
    import-facing QC review

## Open The Code-Backed Surfaces

- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/proof_classes.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/proof_accounting.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/flagship_runs.py`

## Boundary

Proof accounting does not make a workflow trustworthy by itself. It only keeps
the runtime honest about which claims are raw, import-backed, replay-backed, or
simulation-only before knowledge, recommendation, and lab layers build on top
of them.
