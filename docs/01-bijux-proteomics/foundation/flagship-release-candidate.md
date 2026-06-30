---
title: Flagship Release Candidate
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Flagship Release Candidate

The current flagship release-candidate surface is not the whole repository.

It is four bounded outsider-auditable families, one review-grade-bounded
family, and one explicitly narrowed internal-support family.

Outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

Family-level trust in this bundle now assumes paired public benchmark packages
and one published family-transfer report per workflow family, not one unusually
convenient flagship package.

The bundle is stronger than it was at `v0.3.7` because it now rests on a
deeper cross-package chain: broader core scientific surfaces, clearer runtime
rerun packets, explicit knowledge grounding, reviewable recommendation
posture, and consequence-aware lab follow-up. It is still bounded because the
strongest family packet is not the same thing as repository-wide readiness.

## Current Bundle

- bundle id: `flagship-release-candidate-bundle`
- strongest workflow family: `dda`
- outsider-auditable workflow families: `dda`, `dia`, `lfq`, `ptm`, `targeted`
- released outsider-auditable workflow families: `dda`, `dia`, `ptm`, `targeted`
- review-grade-bounded workflow families: `lfq`
- internal-support-only workflow families: `multiplex`

## What The Bundle Proves About Real Product Depth

- core now contributes more than a benchmark wrapper: the flagship families
  lean on deeper sequence, chemistry, identification, quantification, PTM,
  DIA, review, and workflow-contract surfaces.
- runtime now contributes more than one launch command: the bundle assumes
  replay lanes, preflight checks, import-versus-raw honesty, refusal surfaces,
  and artifact-stability expectations.
- knowledge now contributes more than citations in prose: the bundle assumes
  workflow claim grounding, literature audits, and contradiction-aware memory.
- intelligence now contributes more than a final score: the bundle assumes
  recommendation confidence, falsifier-aware review, and explicit downgrade
  posture.
- lab now contributes more than aspirational follow-up: the bundle assumes a
  requested-versus-observed outcome dossier and visible consequence pressure.

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
  - [Why Trust PTM](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-ptm/)
  - [Why Trust Targeted](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-targeted/)
- workflow claim-limit pages:
  - [Why Trust LFQ](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-trust-lfq/)
  - [Why Multiplex Stops At Internal Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-multiplex-stops-at-internal-support/)
  - [Workflow Claim Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-claim-limits/)
- public scrutiny pages:
  - [Release Narrowing Protocol](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-narrowing-protocol/)
  - [Hostile Review Kit](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/hostile-review-kit/)
  - [Independent Rerun Dossiers](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/independent-rerun-dossiers/)
  - [External Review Kits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/external-review-kits/)
  - [Public Artifact Index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/)
  - [Public Artifact Role Matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-role-matrix/)
  - [Why This Repository Is Not Ready Yet](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/why-this-repository-is-not-ready-yet/)
  - [What Would Make This Repository Ready](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-would-make-this-repository-ready/)

The public artifact index is the stable opening-order registry for the bundle.
The public artifact role matrix is the stable coexistence map that shows why
each shipped artifact still exists beside its stronger or weaker neighbors.
The hostile review kit is the stable whole-repository challenge route for the
bundle.
The release narrowing protocol is the stable language-demotion rule set for the
bundle.

Open [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
when the right next question is family comparison instead of bundle inventory.
Open [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
when the right next question is rerunability instead of bundle language.
Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
when the right next question is grounding, recommendation posture, or artifact
role overlap.

## Honest Reading

- `dda` survives one full outsider packet:
  two public packages, one family-transfer report, runtime lane, comparator
  pressure, scientific reading, recommendation packet, independent rerun
  dossier, external review kit, planned lab packet, and one
  requested-versus-observed outcome dossier
- `dia`, `ptm`, and `targeted` now also survive full outsider packets, but
  each authority stays bounded by advisory comparator posture, the measured
  drift recorded in its family-transfer report, the companion rerun dossier,
  external execution limits, or benchmark-simulated requested-versus-observed
  lab consequence
- `lfq` remains review-grade bounded because its external review kit and
  acceptance sheet still show missingness and normalization pressure that
  narrows the stronger outsider-facing sentence
- `lfq` also has an outsider-auditable packet in the narrow sense that its
  benchmark package, runtime lane, grounding route, recommendation packet, and
  consequence route are all public; the released public sentence remains
  review-grade bounded because those public surfaces still document the
  narrowing pressure directly
- `multiplex` has real package and runtime substance, but it is intentionally
  narrowed to internal support only because its companion stress package still
  collapses outsider-facing trust in the published family-transfer report

## Boundary

This page does not authorize repository-wide excellence language. It only names
the strongest current outsider-auditable family set and the internal-support
boundary for the rest.
