---
title: Flagship Acceptance Bars
audience: mixed
type: handbook
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-07
---

# Flagship Acceptance Bars

`bijux-proteomics` now publishes one explicit acceptance sheet per flagship workflow family instead of letting trust posture hide inside a mix of review prose, challenge assets, and release pages.

The machine-readable root is:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-acceptance/`

That root currently ships:

- `dda_acceptance_sheet.json`
- `dia_acceptance_sheet.json`
- `lfq_acceptance_sheet.json`
- `multiplex_acceptance_sheet.json`
- `ptm_acceptance_sheet.json`
- `targeted_acceptance_sheet.json`
- `acceptance_dashboard.json`
- `benchmark_history_ledger.json`
- `acceptance_rationale_dossier.json`

## What The Sheets Measure

Each family sheet publishes five exact bars tied to the real flagship package:

- `dda`: search coverage, protein inference stability, calibration sanity, comparator divergence tolerance, and review-packet promotion.
- `dia`: library dependence, peptide evidence coverage, protein evidence stability, quantitative coherence, and review-packet promotion.
- `lfq`: missingness burden, normalization drift, differential reproducibility, comparator divergence, and recommendation promotion.
- `multiplex`: interference, channel dropout, reference-channel fragility, ratio compression, and downstream review promotion.
- `ptm`: localization quality, ambiguity burden, motif credibility, occupancy stability, and targetability promotion.
- `targeted`: calibration quality, transition interference, heavy-light coherence, carryover posture, and follow-up promotion.

## Current Trust Posture

The dashboard is the short answer:

- `acceptance_dashboard.json` compares current public release language with the earned language from the live sheets.
- trusted bounded families are expected to stay at `outsider_auditable_bounded` only while their sheets pass.
- `multiplex` remains `internal_support_only`, and its sheet is intentionally failing because current imbalance, dropout, and compression pressure do not justify stronger trust.

## Why These Bars Exist

The rationale dossier is the long answer:

- `acceptance_rationale_dossier.json` ties every bar back to comparator pressure, literature-backed threshold anchors, benchmark difficulty, or lab consequence.
- the history ledger records the first published threshold set so later edits cannot quietly become looser without saying so.

## How To Refresh

Run:

```bash
uv run --group dev python -m bijux_proteomics.benchmarks.flagship_acceptance_assets refresh
```

That command rewrites all six family sheets plus the dashboard, threshold-history ledger, and rationale dossier.

## Related Proof Surfaces

- [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
- [Flagship Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-benchmark-assets/)
- [Flagship Challenge Corpus Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-challenge-corpus-catalog/)
