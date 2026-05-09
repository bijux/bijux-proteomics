---
title: Flagship Release Candidate
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Flagship Release Candidate

The current flagship release-candidate surface is not the whole repository.

It is five bounded outsider-auditable families plus one explicitly narrowed
internal-support family.

Outsider-auditable workflow families today: `dda`, `dia`, `lfq`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

Family-level trust in this bundle now assumes paired public benchmark packages
and one published family-transfer report per workflow family, not one unusually
convenient flagship package.

## Current Bundle

- bundle id: `flagship-release-candidate-bundle`
- strongest workflow family: `dda`
- outsider-auditable workflow families: `dda`, `dia`, `lfq`, `ptm`, `targeted`
- internal-support-only workflow families: `multiplex`

## What The Bundle Collects

- benchmark ids:
  - `benchmark:dda_search_reproducibility`
  - `benchmark:dia_library_extraction_consistency`
  - `benchmark:lfq_cohort_repeatability`
  - `benchmark:ptm_localization_consistency`
  - `benchmark:targeted_transition_consistency`
- runtime package ids:
  - `dda-maxquant-pipeline-corpus`
  - `dia-diann-pipeline-corpus`
  - `lfq-cohort-review-corpus`
  - `ptm-localization-review-corpus`
  - `targeted-transition-review-corpus`
- family-transfer scorecard:
  - `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/family_stability_scorecard.json`
- trust pages:
  - [Why Trust DDA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dda/)
  - [Why Trust DIA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dia/)
  - [Why Trust LFQ](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-lfq/)
  - [Why Trust PTM](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-ptm/)
  - [Why Trust Targeted](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-targeted/)
- authority boundary pages:
  - [Multiplex Authority Boundary](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/multiplex-authority-boundary/)
  - [Workflow Authority Matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-authority-matrix/)

## Honest Reading

- `dda` survives one full outsider packet:
  two public packages, one family-transfer report, runtime lane, comparator
  pressure, scientific reading, recommendation packet, planned lab packet, and
  one requested-versus-observed outcome dossier
- `dia`, `lfq`, `ptm`, and `targeted` now also survive full outsider packets,
  but each authority stays bounded by advisory comparator posture, the measured
  drift recorded in its family-transfer report, external execution limits, or
  benchmark-simulated requested-versus-observed lab consequence
- `multiplex` has real package and runtime substance, but it is intentionally
  narrowed to internal support only because its companion stress package still
  collapses outsider-facing trust in the published family-transfer report

## Boundary

This page does not authorize repository-wide excellence language. It only names
the strongest current outsider-auditable family set and the internal-support
boundary for the rest.
