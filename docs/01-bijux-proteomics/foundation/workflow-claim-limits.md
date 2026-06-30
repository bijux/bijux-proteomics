---
title: Workflow Claim Limits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Workflow Claim Limits

This page is the release-facing claim-limit source of truth for the flagship
workflow families.

Outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

Family-level trust now requires two public benchmark packages plus one
published cross-package generalization report. The current scorecard lives at
`packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/family_stability_scorecard.json`.

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

The current lab-consequence evidence is still benchmark-simulated rather than
live wet-lab release proof. It earns bounded consequence language because the
requested-versus-observed loop is now explicit, not because the repository has
already closed real laboratory deployment risk.

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
