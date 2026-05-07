---
title: Flagship Public Benchmark Catalog
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-07
---

# Flagship Public Benchmark Catalog

`bijux-proteomics-core` now publishes one explicit catalog for the flagship
public benchmark packages that downstream review, runtime, knowledge, and lab
surfaces rely on.

The point of this catalog is not volume. It is to make one reviewer ask and one
answer possible:

Which public package exists for this workflow family, what exact artifacts does
it expose, and what authority still stays blocked?

## Current Catalog

- `dda`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, scientific invariants, warning demonstrations
- `dia`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, Spectronaut-style report, Spectronaut-style
    pipeline export, DIA-NN-style pipeline export
- `lfq`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, study-scale feature table, cohort design table
- `multiplex`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, reporter feature table, multiplex design table
- `ptm`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, localization table, PTM feature table, reference
    FASTA, raw spectra
- `targeted`
  - package root:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
  - tracked review surfaces: package manifest, artifact inventory, quality
    sheet, lifecycle record, targeted QC table, approved follow-up packet,
    failed follow-up packet, refused follow-up packet

## What This Catalog Guarantees

- every flagship family has one durable package root instead of scattered proof
  fragments
- every package ships machine-readable package identity, artifact inventory,
  quality posture, and lifecycle posture
- every package also ships a source locator manifest, citation manifest,
  generated-boundary manifest, and rebuild instructions
- every downstream surface can point to one concrete public package path instead
  of describing a benchmark family abstractly

## What This Catalog Does Not Guarantee

- outsider-auditable authority for every workflow family
- live runtime execution for every package
- comparator parity for every package
- decision-grade scientific support across the whole catalog

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_public_packages.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_asset_roots.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_public_package_surface.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_asset_root_surface.py`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages`

## Asset Maintenance

Open [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
when you need the copied-source contract, citation discipline, refresh command,
freshness report, or obsolescence audit for these package roots.
