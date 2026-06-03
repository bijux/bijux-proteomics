---
title: Flagship Challenge Corpus Catalog
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-07
---

# Flagship Challenge Corpus Catalog

`bijux-proteomics-core` now publishes one product-owned challenge root alongside
the public benchmark packages:

`packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/`

The point of this catalog is to keep the punishing evidence visible, not merely
to celebrate that benchmark packages exist. Every challenge root records what
was frozen, what was perturbed, what measured deltas followed, and whether the
workflow, comparator, or review posture survived, weakened, or collapsed.

## Shared Machine-Readable Surface

Every challenge root is governed through:

- `challenge_registry.json`
- one `challenge_manifest.json`
- one revealed report:
  - `blinded_holdout_report.json`, or
  - `perturbation_report.json`
- one local `README.md`

The registry is the first machine-readable proof check:

`packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/challenge_registry.json`

## Blinded Holdouts

The current blinded holdout roots are:

- `dda_blinded_holdout`
- `dia_blinded_holdout`
- `lfq_blinded_holdout`
- `ptm_blinded_holdout`

These roots freeze the main reviewer-facing surfaces first and reveal the hidden
family-transfer truth only after the workflow, comparator, and recommendation
posture is already fixed.

Current holdout limit:

- `multiplex` and `targeted` do not yet have blinded holdout roots here, so the
  challenge corpus is still incomplete even though their perturbation roots now
  exist.

## Perturbation Roots

The current perturbation roots are:

- `dda_calibration_decoy_perturbation`
- `dia_library_dropout_perturbation`
- `lfq_missingness_drift_perturbation`
- `multiplex_reference_bleed_perturbation`
- `ptm_ambiguity_occupancy_perturbation`
- `targeted_interference_carryover_perturbation`

Each perturbation root publishes measured reaction deltas instead of generic
severity prose. The current catalog explicitly covers:

- `dda`: accepted-target loss, accepted-decoy intrusion, contaminant promotion
- `dia`: accepted-precursor dropout, shared-peptide loss,
  library-conditioned comparator shrinkage
- `lfq`: missing-value inflation, batch-drift pressure, differential narrative
  reshuffle
- `multiplex`: reference dropout, channel bleed, carrier-conditioned ratio
  compression
- `ptm`: localization ambiguity, occupancy instability, targetability collapse
- `targeted`: calibrant drift, transition interference, carryover-blocked
  follow-up

## What This Catalog Settles

- whether a workflow family only looks strong on its easiest package
- whether family-transfer claims survive blinded reveal instead of convenient
  hindsight
- whether review posture collapses quickly once calibration, missingness,
  bleed, ambiguity, or carryover pressure is made explicit

## What This Catalog Does Not Settle

- broad outsider-grade authority across every flagship family
- more than one blinded holdout root for the currently covered families
- multiplex or targeted holdout discipline
- long-run acceptance bars or release gating by challenge-failure history

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_challenge_corpora.py`
- `packages/bijux-proteomics-core/src/bijux_proteomics/benchmarks/flagship_challenge_assets.py`
- `packages/bijux-proteomics-core/tests/benchmarks/test_flagship_challenge_corpora_surface.py`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora`

Refresh the copied challenge roots with
`uv run --group dev python -m bijux_proteomics.benchmarks.flagship_challenge_assets refresh`.

## Neighbor Surfaces

Open [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
when you need the paired public package roots that these challenges are trying
to break.

Open [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
when you need the copied-source contract, citation discipline, rebuild command,
freshness report, and obsolescence audit behind the public benchmark roots.
