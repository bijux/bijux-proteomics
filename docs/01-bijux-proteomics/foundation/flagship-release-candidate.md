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

It is two outsider-auditable families, `dda` and `dia`, plus three explicitly
incomplete review families that are shipped alongside their blocker pages
instead of being flattened into optimistic release language.

## Current Bundle

- bundle id: `flagship-release-candidate-bundle`
- strongest workflow family: `dda`
- outsider-auditable workflow families: `dda`, `dia`
- blocked workflow families: `lfq`, `ptm`, `targeted`

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
  - `quant_review-blocked-runtime-path`
  - `ptm_review-blocked-runtime-path`
- trust pages:
  - [Why Trust DDA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dda/)
  - [Why Trust DIA](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-dia/)
  - [Why Trust LFQ](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-lfq/)
  - [Why Trust PTM](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-ptm/)
  - [Why Trust Targeted](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-targeted/)
- distrust pages:
  - [Why Not Trust LFQ Yet](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-not-trust-lfq-yet/)
  - [Why Not Trust PTM Yet](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-not-trust-ptm-yet/)
  - [Why Not Trust Targeted Yet](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-not-trust-targeted-yet/)

## Honest Reading

- `dda` survives one full outsider packet:
  public package, runtime lane, comparator pressure, scientific reading,
  recommendation packet, and lab packet
- `dia` now also survives one full outsider packet, but its authority stays
  bounded by library-conditioned import review, advisory claim support, and
  execution steps that still sit outside the repository proof boundary
- `lfq`, `ptm`, and `targeted` are currently stronger as explicit refusal
  surfaces than as positive release families

## Boundary

This page does not authorize repository-wide excellence language. It only names
the strongest current outsider-auditable family and the blocker pages for the
rest.
