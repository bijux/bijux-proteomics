---
title: Release Narrowing Protocol
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Release Narrowing Protocol

This page is generated from live release evidence. It records how workflow-family language narrows automatically when benchmark asset quality, black-box rerunability, acceptance bars, or consequence realism weaken.

## Ordered Rules

### `benchmark-asset-quality`

- trigger surface: release-readiness matrix
- narrowed language: `review_grade_bounded`
- rationale: If benchmark asset quality is blocked, family language falls back behind the current outsider-auditable sentence.

### `black-box-rerunability`

- trigger surface: release-readiness matrix plus rerun surfaces
- narrowed language: `review_grade_bounded`
- rationale: If the rerun dossier or external review kit stops surviving hostile review, the family loses outsider-auditable language immediately.

### `acceptance-bars`

- trigger surface: flagship acceptance dashboard
- narrowed language: `review_grade_bounded`
- rationale: If the earned acceptance language drops below the requested public language, the family inherits the weaker earned language.

### `consequence-evidence`

- trigger surface: release-readiness matrix
- narrowed language: `review_grade_bounded`
- rationale: If consequence realism is blocked, recommendation-facing workflow language narrows until downstream evidence and lab consequence are coherent again.

## Current Workflow Decisions

| workflow family | requested language | allowed language | active rules |
| --- | --- | --- | --- |
| `dda` | `outsider_auditable_bounded` | `review_grade_bounded` | `benchmark-asset-quality` |
| `dia` | `outsider_auditable_bounded` | `review_grade_bounded` | `benchmark-asset-quality` |
| `lfq` | `outsider_auditable_bounded` | `review_grade_bounded` | `benchmark-asset-quality` |
| `multiplex` | `internal_support_only` | `internal_support_only` | `acceptance-bars` |
| `ptm` | `outsider_auditable_bounded` | `review_grade_bounded` | `benchmark-asset-quality` |
| `targeted` | `outsider_auditable_bounded` | `review_grade_bounded` | `benchmark-asset-quality` |

## Evidence Behind The Current Decisions

### `dda`

- requested language: `outsider_auditable_bounded`
- allowed language: `review_grade_bounded`
- active reasons: benchmark asset quality is currently blocked in the release-readiness matrix
- evidence paths: `configs/package-governance/scientific-release-workflows.toml`, `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`, `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

### `dia`

- requested language: `outsider_auditable_bounded`
- allowed language: `review_grade_bounded`
- active reasons: benchmark asset quality is currently blocked in the release-readiness matrix
- evidence paths: `configs/package-governance/scientific-release-workflows.toml`, `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`, `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

### `lfq`

- requested language: `outsider_auditable_bounded`
- allowed language: `review_grade_bounded`
- active reasons: benchmark asset quality is currently blocked in the release-readiness matrix
- evidence paths: `configs/package-governance/scientific-release-workflows.toml`, `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`, `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

### `multiplex`

- requested language: `internal_support_only`
- allowed language: `internal_support_only`
- active reasons: acceptance bars earn weaker language than the current requested sentence
- evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/multiplex_acceptance_sheet.json`

### `ptm`

- requested language: `outsider_auditable_bounded`
- allowed language: `review_grade_bounded`
- active reasons: benchmark asset quality is currently blocked in the release-readiness matrix
- evidence paths: `configs/package-governance/scientific-release-workflows.toml`, `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`, `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

### `targeted`

- requested language: `outsider_auditable_bounded`
- allowed language: `review_grade_bounded`
- active reasons: benchmark asset quality is currently blocked in the release-readiness matrix
- evidence paths: `configs/package-governance/scientific-release-workflows.toml`, `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`, `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`
