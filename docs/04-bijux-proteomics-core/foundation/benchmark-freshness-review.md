---
title: Benchmark Freshness Review
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Benchmark Freshness Review

This page records whether each flagship workflow family still has a current benchmark review window, whether the checked freshness report still records its copied snapshots and remote references as available, and whether a stronger checked replacement is already recorded. Release narrowing consumes these rows directly when freshness drops below the current public sentence.

## Coverage

| workflow family | review state | remote reference state | requested language | release language floor |
| --- | --- | --- | --- | --- |
| `dda` | `current` | `recorded_available` | `outsider_auditable_bounded` | `outsider_auditable_bounded` |
| `dia` | `current` | `recorded_available` | `outsider_auditable_bounded` | `outsider_auditable_bounded` |
| `lfq` | `current` | `recorded_available` | `outsider_auditable_bounded` | `outsider_auditable_bounded` |
| `multiplex` | `current` | `recorded_available` | `internal_support_only` | `internal_support_only` |
| `ptm` | `current` | `recorded_available` | `outsider_auditable_bounded` | `outsider_auditable_bounded` |
| `targeted` | `current` | `recorded_available` | `outsider_auditable_bounded` | `outsider_auditable_bounded` |

## Family Review

### `dda`

- benchmark title: DDA reviewable public benchmark package
- public dataset identity: tracked raw-like spectrum plus paired MaxQuant and MSFragger exported-result snapshots inside one outsider-readable DDA package
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`
- last reviewed on: `2026-05-05`
- freshness window: `365` days
- freshness due on: `2027-05-05`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the one-run DDA package with a multi-run public DDA asset root that still preserves paired comparator confrontation.
- requested release language: `outsider_auditable_bounded`
- release language floor: `outsider_auditable_bounded`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

### `dia`

- benchmark title: DIA library review public benchmark package
- public dataset identity: tracked Spectronaut-style and DIA-NN-style exported-result snapshots with explicit library-conditioned settings and confrontation scope
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`
- last reviewed on: `2026-05-07`
- freshness window: `365` days
- freshness due on: `2027-05-07`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the import-backed DIA package with a raw-executable or chromatogram-backed DIA asset root.
- requested release language: `outsider_auditable_bounded`
- release language floor: `outsider_auditable_bounded`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

### `lfq`

- benchmark title: LFQ cohort review public benchmark package
- public dataset identity: tracked study-scale feature and cohort-design snapshots with explicit missingness and repeatability boundaries
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`
- last reviewed on: `2026-05-07`
- freshness window: `365` days
- freshness due on: `2027-05-07`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the current LFQ package with a pair of public cohort packages that expose stronger truth and generalization pressure.
- requested release language: `outsider_auditable_bounded`
- release language floor: `outsider_auditable_bounded`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

### `multiplex`

- benchmark title: Multiplex TMTpro public benchmark package
- public dataset identity: tracked TMTpro feature and design snapshots with explicit reporter-channel, imbalance, and missing-channel pressure
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`
- last reviewed on: `2026-05-07`
- freshness window: `365` days
- freshness due on: `2027-05-07`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the current TMTpro package with a broader multiplex asset root that includes runtime and follow-up consequence closure.
- requested release language: `internal_support_only`
- release language floor: `internal_support_only`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

### `ptm`

- benchmark title: PTM localization public benchmark package
- public dataset identity: tracked localization, PTM feature, raw-spectrum, and sequence-context snapshots with explicit ambiguity limits
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`
- last reviewed on: `2026-05-07`
- freshness window: `365` days
- freshness due on: `2027-05-07`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the current PTM package with one that broadens PTM-family scope and closes runtime plus comparator gaps.
- requested release language: `outsider_auditable_bounded`
- release language floor: `outsider_auditable_bounded`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`

### `targeted`

- benchmark title: Targeted transition public benchmark package
- public dataset identity: tracked chromatogram-shaped QC table plus approved, failed, and refused follow-up packet snapshots
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`
- last reviewed on: `2026-05-07`
- freshness window: `365` days
- freshness due on: `2027-05-07`
- review state: `current`
- remote reference state: `recorded_available`
- stronger replacement recorded: `no`
- replacement note: No stronger checked replacement is recorded yet. Replace the current targeted package with a raw-executable targeted asset root that includes calibration and comparator closure.
- requested release language: `outsider_auditable_bounded`
- release language floor: `outsider_auditable_bounded`
- blockers: none
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/source_locator_manifest.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/freshness_report.json`, `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/obsolescence_audit.json`
