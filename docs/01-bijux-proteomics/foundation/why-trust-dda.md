---
title: Why Trust DDA
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Why Trust DDA

This page is about the current flagship `dda` result surface.

It does not say DDA is solved in general. It says the repository now ships two
public DDA packages and one published cross-package report, so a skeptical
reviewer can inspect whether the main DDA claims survive beyond one unusually
convenient package.

What is stronger than before is the surrounding chain: broader core review
surfaces, explicit runtime packaging, knowledge grounding, downgrade-aware
recommendation, and visible consequence posture. What stays weaker is the live
execution boundary.

## Open First

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/README.md`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/scientific_invariants.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/warning_demonstrations.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`
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

## What The Reader Is Really Auditing

- whether adapter-normalized DDA evidence remains interpretable after engine
  translation
- whether cross-engine drift is shown instead of hidden
- whether the package, runtime lane, and recommendation posture all admit the
  same downgrade pressure

## Exact Claims

- adapter-normalized DDA evidence preserves target-decoy semantics across the
  pinned fixture corpus
- review-ready DDA evidence retains reviewed-proteome grounding and explicit
  field-loss accounting

## Why This Is Trustworthy Now

- the public package is inspectable from tracked files alone
- one companion public package keeps DDA trust from depending only on the
  MaxQuant-versus-MSFragger pairing
- the primary MaxQuant import and MSFragger comparator export are both shipped
- the companion Comet-versus-Sage package ships a second engine pairing and a
  published family-transfer report at
  `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`
- numeric invariants and one concrete protein-rollup warning are published
- runtime, knowledge, intelligence, and lab all point at the same family

## Why The Public Sentence Still Narrows

- DDA still lacks in-repo live-engine rerun parity
- the strongest current route remains import-backed rather than raw-executable
- the companion package proves the repository is willing to surface rollup
  drift instead of flattening it into a success story

## Limits That Stay In Force

- this is not live-engine rerun parity
- this is not broad cohort-grade DDA authority
- the family-transfer report still shows that protein-facing confidence weakens
  under the companion engine pairing
- protein-facing claims stay downgrade-heavy because the comparator package
  demonstrates cross-engine rollup drift directly

## Evidence Grounding

- sentence grounding and unsupported-claim review:
  [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
- citation freshness, bibliography export, and gap audits:
  [Workflow Literature Audits](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-literature-audits/)
