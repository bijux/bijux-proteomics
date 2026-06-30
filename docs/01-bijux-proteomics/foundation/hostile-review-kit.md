---
title: Hostile Review Kit
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Hostile Review Kit

The repository currently promises one bounded proteomics review system: outsider-auditable workflow families `dda`, `dia`, `ptm`, `targeted` and internal-support-only workflow families `multiplex`. No broader release language is earned.

This page is the shortest whole-repository challenge route for a skeptical expert. It starts from the root promise, then moves directly into the strongest shipped workflow families, their paired rerun dossiers, and the current release boundary.

The reason this page exists is that the repository now has enough depth that a
skeptical reader can challenge real scientific and runtime claims, not only
docs phrasing. The hostile route is how the repository proves that its
strongest public sentences can be audited without private commentary.

It is also the page that stops the stronger current product from being judged
only by its most polished surfaces. The hostile route makes benchmark,
rerunability, grounding, recommendation, and release blockers visible in one
opening order so the review starts at the hardest route, not the nicest prose.

## Open In This Order

- `docs/01-bijux-proteomics/foundation/release-readiness-matrix.md`
- `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`
- `docs/01-bijux-proteomics/foundation/public-artifact-index.md`
- `docs/01-bijux-proteomics/foundation/why-this-repository-is-not-ready-yet.md`
- `docs/01-bijux-proteomics/foundation/what-would-make-this-repository-ready.md`

## Root Bundle

- bundle id: `flagship-release-candidate-bundle`
- root challenge: ask whether every public sentence stays inside the current outsider-auditable bounded family set and its published limits
- first refusal: if a claim cannot be traced from the root page into one flagship family packet, its rerun dossier, and its external review kit, reject the sentence

## What This Route Is Testing

- whether repository-wide wording stays behind the strongest current family
  packets
- whether each public workflow sentence survives benchmark, rerun, review, and
  consequence challenge together
- whether blocker pages stay visible before anyone widens the language by
  interpretation

## Why This Route Matters More Now

- the repository now has enough real scientific and runtime substance that a
  skeptical reader can challenge concrete claims instead of only documentation
  style
- stronger benchmark and rerun packets make it easier to overread the current
  release ceiling unless the blocker pages stay in the opening order
- the hostile route proves whether the current flagship sentence survives the
  hardest reading sequence the repository itself can justify

## Family Challenge Lanes

| workflow family | public language | outsider packet | independent rerun dossier | external review kit | trust page |
| --- | --- | --- | --- | --- | --- |
| `dda` | `outsider_auditable_bounded` | `outsider_review:dda` | `artifacts/intelligence/independent-reruns/dda_independent_rerun_dossier.json` | `artifacts/intelligence/external-review-kits/dda_external_review_kit.json` | `docs/01-bijux-proteomics/foundation/why-trust-dda.md` |
| `dia` | `outsider_auditable_bounded` | `outsider_review:dia` | `artifacts/intelligence/independent-reruns/dia_independent_rerun_dossier.json` | `artifacts/intelligence/external-review-kits/dia_external_review_kit.json` | `docs/01-bijux-proteomics/foundation/why-trust-dia.md` |
| `ptm` | `outsider_auditable_bounded` | `outsider_review:ptm` | `artifacts/intelligence/independent-reruns/ptm_independent_rerun_dossier.json` | `artifacts/intelligence/external-review-kits/ptm_external_review_kit.json` | `docs/01-bijux-proteomics/foundation/why-trust-ptm.md` |
| `targeted` | `outsider_auditable_bounded` | `outsider_review:targeted` | `artifacts/intelligence/independent-reruns/targeted_independent_rerun_dossier.json` | `artifacts/intelligence/external-review-kits/targeted_external_review_kit.json` | `docs/01-bijux-proteomics/foundation/why-trust-targeted.md` |

## How To Challenge Each Family

### `dda`

- challenge question: Do the outsider-facing DDA claims survive a second checked package with a different search-engine pairing instead of one convenient import lane?
- packet id: `outsider_review:dda`
- opening order: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/README.md`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/README.md`, `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`, `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`
- exact claims: adapter-normalized DDA evidence preserves target-decoy semantics across the pinned fixture corpus, review-ready DDA evidence retains reviewed-proteome grounding and explicit field-loss accounting
- current limits: Compare the primary MaxQuant import path against the paired MSFragger comparator export inside the tracked DDA package., Preserve target-decoy visibility and explicit protein-rollup caution rather than flattening DDA review into engine-agnostic certainty., The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary., The strongest shipped rerun lane is still import-backed rather than a raw external-engine execution owned by this repository., comparator drift or missing external execution parity still materially limits this public workflow claim

### `dia`

- challenge question: Do the outsider-facing DIA claims survive a second execution lane with a different vendor-conditioned matrix surface?
- packet id: `outsider_review:dia`
- opening order: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/README.md`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/README.md`, `packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py`, `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`
- exact claims: DIA adapter normalization preserves library-conditioned transition semantics across the pinned export corpus, DIA review surfaces keep capability limits explicit instead of implying vendor-pipeline parity
- current limits: Compare adapter-normalized outputs against the tracked DIA public package because direct DIA-NN or Spectronaut execution is outside repo scope., Keep SWATH-style transition semantics aligned with the published DIA method reference., The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary., The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions., comparator drift or missing external execution parity still materially limits this public workflow claim, the current reproduction story still depends on execution steps that remain outside the repository proof boundary

### `ptm`

- challenge question: Do the outsider-facing PTM claims survive a harsher localization ambiguity lane instead of one clean flagship corpus?
- packet id: `outsider_review:ptm`
- opening order: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/README.md`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/README.md`, `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`, `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`
- exact claims: PTM review preserves localization confidence, ambiguity, and PSI-MOD grounding across the pinned phospho-oriented fixture, PTM benchmark outputs separate localized evidence from broader occupancy or regulatory claims
- current limits: Compare localization handling against the checked-in PTM localization fixture because direct rescoring engines are not executed in the repo test path., Retain Ascore-style ambiguity framing and PSI-MOD grounding in the resulting claims., The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary., The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions., comparator drift or missing external execution parity still materially limits this public workflow claim

### `targeted`

- challenge question: Do the outsider-facing targeted claims survive a carryover and reuse pressure lane instead of one convenient transition package?
- packet id: `outsider_review:targeted`
- opening order: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/README.md`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/README.md`, `packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py`, `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`
- exact claims: Targeted benchmark outputs preserve transition-level QC evidence and explicit protein-inference caution across the bundled chromatogram fixture, Targeted review can support operator-facing QC interpretation without pretending to prove vendor-parity targeted biology
- current limits: Compare targeted QC handling against the tracked targeted public package and published protein-inference caution rather than claiming direct vendor chromatogram parity., Keep support claims scoped to transition-level evidence retention and cautious rollup semantics., The dossier still describes repository-owned rerun lanes, not an untracked third-party reproduction outside the repository boundary., The strongest shipped rerun lane is raw-executable inside the repository, but vendor-parity and broader ecosystem replay are still separate questions., comparator drift or missing external execution parity still materially limits this public workflow claim

## Non-Negotiable Reading Rule

If the current release-readiness matrix still shows blocked categories, no reviewer should widen the root promise by interpretation alone. The blocker pages below are part of the review kit because they keep the failure modes visible before maintainers start explaining them away.

## Strongest Honest Outcome

- if the reader still lands on a blocked category, the route worked
- if the strongest family packet survives but the repository-wide sentence
  still narrows, that is the intended result
- this page is successful when it prevents language drift, not when it makes
  the repository sound more complete

## Honest Result

If this route still lands on a blocked category, the stronger sentence is not
earned yet. That is not a documentation failure. It is the intended behavior of
the hostile review surface.
