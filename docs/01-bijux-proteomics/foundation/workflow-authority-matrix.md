---
title: Workflow Authority Matrix
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Workflow Authority Matrix

This page is the release-facing authority source of truth for the flagship
workflow families.

Outsider-auditable workflow families today: `dda`, `dia`, `lfq`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

Family-level trust now requires two public benchmark packages plus one
published cross-package generalization report. The current scorecard lives at
`packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/family_stability_scorecard.json`.

## Current Authority

| Workflow | Internal benchmark-backed | Raw-executable | Externally cross-checked | Outsider-auditable | Lab-consequential | Public language |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `dda` | yes | no | yes | yes | yes | bounded outsider-auditable |
| `dia` | yes | yes | yes | yes | yes | bounded outsider-auditable |
| `lfq` | yes | yes | yes | yes | yes | bounded outsider-auditable |
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
  reading, recommendation packet, lab packet, and the family generalization
  report can be opened together by a skeptical reviewer
- `lab-consequential` means a dedicated flagship lab packet exists, even when
  the packet still keeps the family exploratory-only

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
