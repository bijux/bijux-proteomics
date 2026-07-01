---
title: Workflow Claim Limits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Workflow Claim Limits

This page is the release-facing claim-limit source of truth for the flagship
workflow families.

Outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.
Released outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.
Full outsider-readable family packets today: `dda`, `dia`, `lfq`, `ptm`, `targeted`.

Family-level trust now requires two public benchmark packages plus one
published cross-package generalization report. The current scorecard lives at
`packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/family_stability_scorecard.json`.

What changed since `v0.3.7` is not only wording. The matrix now sits on a
deeper chain of proof: broader core scientific surfaces, clearer runtime
rerun lanes, explicit knowledge grounding, recommendation posture, and visible
lab consequence pressure. That means the repository can now distinguish between
families that have a full outsider-readable packet and families whose released
sentence must still stay narrower.

The point of this matrix is to keep that stronger depth from being flattened
into one generic trust label. A family can now have meaningful benchmark,
runtime, grounding, recommendation, and consequence surfaces while still
stopping short of the broadest released sentence.

## What This Matrix Governs

- what the repository can publicly say today for each workflow family
- which family has a full benchmark, runtime, grounding, recommendation, and
  consequence packet
- which family still narrows at the released sentence because one part of that
  packet remains downgrade-heavy
- which family stops at internal support even though code, runtime, and public
  benchmark substance exist

The distinction that matters most now is this:

- `outsider-auditable` is the stronger release-language set
- `full outsider-readable family packets` is the wider proof-packet set
- LFQ currently belongs to the second set but not the first

## Why This Distinction Matters

- it keeps the repository from flattening all strong-looking family packets
  into one trust label
- it explains why a public packet can be openable and still remain narrowed at
  release time
- it makes clear that consequence and burden surfaces can still veto broader
  family language

## Current Limits

| Workflow | Internal benchmark-backed | Raw-executable | Externally cross-checked | Outsider-auditable | Lab-consequential | Public language |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `dda` | yes | no | yes | yes | yes | bounded outsider-auditable |
| `dia` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `lfq` | yes | yes | yes | no | yes | review-grade bounded |
| `multiplex` | yes | yes | no | no | no | internal support only |
| `ptm` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `targeted` | yes | yes | yes | yes | yes | bounded outsider-auditable |

## How To Read This

- `internal benchmark-backed` means a tracked flagship public package exists
  under `benchmark-assets/flagship-public-packages/`
- `raw-executable` means the strongest current runtime lane runs the tracked
  package directly instead of stopping at an import-only bridge
- `externally cross-checked` means public comparator posture is at least
  advisory rather than refused
- `outsider-auditable` means the benchmark package, runtime lane, scientific
  reading, recommendation packet, planned lab packet, requested-versus-observed
  outcome dossier, and the family generalization report can be opened together
  by a skeptical reviewer
- `review-grade bounded` means the benchmark, runtime, and review surfaces stay
  usable, but the current external review kit or acceptance pressure still
  narrows the stronger outsider-facing sentence
- `lab-consequential` means a dedicated flagship lab packet, one shipped
  requested-versus-observed outcome dossier, and one assay-worth-it ledger row
  all exist together

## What Outsider-Auditable Still Refuses

- it does not mean universal transfer across cohorts, instruments, study
  designs, or vendor-conditioned execution paths
- it does not mean the runtime lane is equally strong for every family
- it does not mean the strongest analytical sentence automatically becomes a
  stronger lab consequence sentence

## What Review-Grade Bounded Still Means

- the family is real enough to inspect through benchmark, runtime, grounding,
  and recommendation surfaces
- the family is not weak or fake; it is explicitly narrowed by visible
  pressure that still survives challenge
- the narrower released sentence is part of the product honesty, not a
  contradiction in the docs

The current lab-consequence evidence is still benchmark-simulated rather than
live wet-lab release proof. It earns bounded consequence language because the
requested-versus-observed loop is now explicit, not because the repository has
already closed real laboratory deployment risk.

## Why LFQ Still Narrows At Release Time

- LFQ now has a full outsider-auditable packet in the narrow sense: public
  benchmark packages, runtime lane, grounding route, recommendation posture,
  requested-versus-observed outcome dossier, and assay-worth-it ledger row
- the released sentence still remains review-grade bounded because missingness,
  normalization pressure, and sparse-cohort transfer risk remain visible in
  its own external review and acceptance surfaces
- this is intentional honesty rather than inconsistency: the packet is public,
  and the narrowing pressure is public too

## Why This Matrix Matters More Now

- the repository can now show several family packets with real outsider-facing
  review substance, so the release boundary has to be explicit instead of
  implied
- stronger public benchmark and rerun surfaces make overclaiming easier unless
  one page still names the narrower sentence exactly
- consequence pressure now matters enough that a family can look analytically
  strong and still need a weaker released sentence

## Reader Use

- use this page when one trust page sounds strong and you need the release
  boundary in one place
- use it to distinguish family-packet breadth from released family language
- use it before widening workflow language in changelogs, READMEs, or release
  summaries

## Family Transfer Evidence

- `dda`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json`
- `dia`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package/cross_package_generalization.json`
- `lfq`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package/cross_package_generalization.json`
- `multiplex`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package/cross_package_generalization.json`
- `ptm`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package/cross_package_generalization.json`
- `targeted`
  - companion package:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
  - generalization report:
    `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package/cross_package_generalization.json`

## Boundary

This matrix does not grant elite language. It only narrows what each workflow
family can honestly claim today.
