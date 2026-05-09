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
- independent rerun dossiers:
  - `artifacts/intelligence/independent-reruns/dda_independent_rerun_dossier.json`
  - `artifacts/intelligence/independent-reruns/dia_independent_rerun_dossier.json`
  - `artifacts/intelligence/independent-reruns/lfq_independent_rerun_dossier.json`
  - `artifacts/intelligence/independent-reruns/ptm_independent_rerun_dossier.json`
  - `artifacts/intelligence/independent-reruns/targeted_independent_rerun_dossier.json`
- external review kits:
  - `artifacts/intelligence/external-review-kits/dda_external_review_kit.json`
  - `artifacts/intelligence/external-review-kits/dia_external_review_kit.json`
  - `artifacts/intelligence/external-review-kits/lfq_external_review_kit.json`
  - `artifacts/intelligence/external-review-kits/ptm_external_review_kit.json`
  - `artifacts/intelligence/external-review-kits/targeted_external_review_kit.json`
- trust pages:
  - [Why Trust DDA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dda/)
  - [Why Trust DIA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dia/)
  - [Why Trust LFQ](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-lfq/)
  - [Why Trust PTM](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-ptm/)
  - [Why Trust Targeted](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-targeted/)
- authority boundary pages:
  - [Multiplex Authority Boundary](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/multiplex-authority-boundary/)
  - [Workflow Authority Matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-authority-matrix/)
- public scrutiny pages:
  - [Independent Rerun Dossiers](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/independent-rerun-dossiers/)
  - [External Review Kits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/external-review-kits/)
  - [Public Artifact Index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/)
  - [What Breaks Elite Trust](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-breaks-elite-trust/)
  - [What Earns Elite Trust Next](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-earns-elite-trust-next/)

The public artifact index is the stable opening-order registry for the bundle.

## Honest Reading

- `dda` survives one full outsider packet:
  two public packages, one family-transfer report, runtime lane, comparator
  pressure, scientific reading, recommendation packet, independent rerun
  dossier, external review kit, planned lab packet, and one
  requested-versus-observed outcome dossier
- `dia`, `lfq`, `ptm`, and `targeted` now also survive full outsider packets,
  but each authority stays bounded by advisory comparator posture, the measured
  drift recorded in its family-transfer report, the companion rerun dossier,
  external execution limits, or benchmark-simulated requested-versus-observed
  lab consequence
- `multiplex` has real package and runtime substance, but it is intentionally
  narrowed to internal support only because its companion stress package still
  collapses outsider-facing trust in the published family-transfer report

## Boundary

This page does not authorize repository-wide excellence language. It only names
the strongest current outsider-auditable family set and the internal-support
boundary for the rest.
