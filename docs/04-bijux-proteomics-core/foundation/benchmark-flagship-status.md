---
title: Benchmark Flagship Status
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Benchmark Flagship Status

This page re-evaluates which public benchmark roots still deserve flagship naming. The promotion gate requires complete asset audit coverage, rebuild discipline, licensing story, comparability notes, and rerun-kit coverage before a root may keep `flagship` in its durable designation.

Reference surfaces:

- `docs/04-bijux-proteomics-core/foundation/benchmark-licensing-and-redistribution.md`
- `docs/04-bijux-proteomics-core/foundation/benchmark-incompleteness-ledger.md`
- `docs/09-bijux-proteomics-runtime/benchmark-rerun-kits.md`
- `docs/09-bijux-proteomics-runtime/benchmark-comparability-matrix.md`

| workflow family | package role | designation | eligible |
| --- | --- | --- | --- |
| `dda` | primary flagship package | `flagship_primary_outsider_auditable` | yes |
| `dda` | companion generalization package | `generalization_companion` | yes |
| `dia` | primary flagship package | `flagship_primary_outsider_auditable` | yes |
| `dia` | companion generalization package | `generalization_companion` | yes |
| `lfq` | primary flagship package | `flagship_primary_outsider_auditable` | yes |
| `lfq` | companion generalization package | `generalization_companion` | yes |
| `multiplex` | primary flagship package | `flagship_primary_internal_support` | yes |
| `multiplex` | companion generalization package | `generalization_companion` | yes |
| `ptm` | primary flagship package | `flagship_primary_outsider_auditable` | yes |
| `ptm` | companion generalization package | `generalization_companion` | yes |
| `targeted` | primary flagship package | `flagship_primary_outsider_auditable` | yes |
| `targeted` | companion generalization package | `generalization_companion` | yes |

## Current Review

### `dda`: primary flagship package

- package id: `flagship_public_package:dda_reviewable_run`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- designation: `flagship_primary_outsider_auditable`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- no in-repo live-engine rerun parity
- one-run package cannot authorize broad production-cohort DDA claims

### `dda`: companion generalization package

- package id: `public_companion_package:dda_cross_engine_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- no live-engine rerun parity
- generalization remains bounded to two small exported-result packages

### `dia`: primary flagship package

- package id: `flagship_public_package:dia_library_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- designation: `flagship_primary_outsider_auditable`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- no chromatogram-level vendor parity
- library incompleteness and absent-peptide consequences still block broader biological confidence

### `dia`: companion generalization package

- package id: `public_companion_package:dia_matrix_shift_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- protein-evidence transfer remains weaker than precursor-level review transfer
- library-conditioned authority still caps the family posture

### `lfq`: primary flagship package

- package id: `flagship_public_package:lfq_cohort_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- designation: `flagship_primary_outsider_auditable`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- no stronger public truth package for accuracy beyond repeatability
- generalization beyond the current cohort package remains explicitly bounded

### `lfq`: companion generalization package

- package id: `public_companion_package:lfq_sparse_contrast_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- effect-direction confidence weakens under sparser contrast
- family authority remains bounded rather than decision-grade

### `multiplex`: primary flagship package

- package id: `flagship_public_package:multiplex_tmtpro_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
- designation: `flagship_primary_internal_support`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Multiplex remains flagship-visible but internal-support only because public workflow language is intentionally narrower.
- no multiplex lab packet or outsider decision brief family
- multiplex authority is intentionally kept out of the outsider-facing flagship set

### `multiplex`: companion generalization package

- package id: `public_companion_package:multiplex_channel_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- Multiplex remains flagship-visible but internal-support only because public workflow language is intentionally narrower.
- multiplex still lacks outsider review and lab consequence posture
- public release language remains internal-support only even with a second package

### `ptm`: primary flagship package

- package id: `flagship_public_package:ptm_localization_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- designation: `flagship_primary_outsider_auditable`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- occupancy and regulatory interpretation still remain narrower than localization evidence
- PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning

### `ptm`: companion generalization package

- package id: `public_companion_package:ptm_ambiguity_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- targetability weakens materially under ambiguity stress
- family authority remains bounded rather than decision-grade

### `targeted`: primary flagship package

- package id: `flagship_public_package:targeted_transition_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- designation: `flagship_primary_outsider_auditable`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- vendor-parity and calibration-clean authority are still outside the current proof boundary
- targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty

### `targeted`: companion generalization package

- package id: `public_companion_package:targeted_carryover_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`
- designation: `generalization_companion`
- asset audit complete: yes
- rebuild path complete: yes
- licensing story complete: yes
- comparability complete: yes
- rerun kit complete: yes
- eligible for designation: yes

- Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming.
- stronger carryover pressure weakens promotion confidence
- family authority remains bounded by calibration and vendor-parity limits
