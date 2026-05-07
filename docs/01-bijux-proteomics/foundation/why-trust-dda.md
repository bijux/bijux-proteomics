---
title: Why Trust DDA
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Why Trust DDA

This page is about the current flagship `dda` result surface.

It does not say DDA is solved in general. It says the repository now ships one
outsider-auditable DDA family that a skeptical reviewer can inspect from files,
runtime lineage, comparator pressure, decision posture, and lab consequence.

## Open First

- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/README.md`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/artifact_inventory.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/scientific_invariants.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/warning_demonstrations.json`
- `packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`

## Current Trust Earned

- `outsider_review:dda` is complete enough to audit end to end.
- benchmark evidence tier is `external_reproduction_package`.
- the runtime package `dda-maxquant-pipeline-corpus` is real and currently
  `import_only`, not imaginary execution.
- public claim support is still `advisory`, which means the downgrade is part
  of the trusted surface, not a hidden embarrassment.
- the recommendation posture is `recommend_with_downgrade`.
- the lab posture is `exploratory_only`.

## Exact Claims

- adapter-normalized DDA evidence preserves target-decoy semantics across the
  pinned fixture corpus
- review-ready DDA evidence retains reviewed-proteome grounding and explicit
  field-loss accounting

## Why This Is Trustworthy Now

- the public package is inspectable from tracked files alone
- the primary MaxQuant import and MSFragger comparator export are both shipped
- numeric invariants and one concrete protein-rollup warning are published
- runtime, knowledge, intelligence, and lab all point at the same family

## Limits That Stay In Force

- this is not live-engine rerun parity
- this is not broad cohort-grade DDA authority
- protein-facing claims stay downgrade-heavy because the comparator package
  demonstrates cross-engine rollup drift directly
