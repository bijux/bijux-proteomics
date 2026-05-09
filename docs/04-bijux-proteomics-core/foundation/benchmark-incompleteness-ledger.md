---
title: Benchmark Incompleteness Ledger
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-05-09
---

# Benchmark Incompleteness Ledger

This ledger records why the current benchmark roots still cap public trust language. It is intentionally repetitive: each package repeats its live blockers, realism limits, failure conditions, and non-transfer zones so a reviewer does not need to infer those limits from prose alone.

## Package Summary

| workflow family | package role | quality blockers | non-transfer zones |
| --- | --- | --- | --- |
| `dda` | primary flagship package | `2` | `2` |
| `dda` | companion generalization package | `2` | `2` |
| `dia` | primary flagship package | `2` | `2` |
| `dia` | companion generalization package | `2` | `2` |
| `lfq` | primary flagship package | `2` | `2` |
| `lfq` | companion generalization package | `2` | `2` |
| `multiplex` | primary flagship package | `2` | `2` |
| `multiplex` | companion generalization package | `2` | `2` |
| `ptm` | primary flagship package | `2` | `2` |
| `ptm` | companion generalization package | `2` | `2` |
| `targeted` | primary flagship package | `2` | `2` |
| `targeted` | companion generalization package | `2` | `2` |

## Live Incompleteness Entries

### `dda`: primary flagship package

- package id: `flagship_public_package:dda_reviewable_run`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run`

Quality blockers:

- no in-repo live-engine rerun parity
- one-run package cannot authorize broad production-cohort DDA claims

Weakness notes:

- The tracked DDA package is still smaller and cleaner than a production multi-run search corpus.
- The package demonstrates protein-rollup drift directly, but it still does not prove live-engine calibration parity.

Fixture realism limits:

- The public package is still a one-run imported-result surface rather than a broader cohort-grade DDA benchmark.
- The package demonstrates cross-engine drift but does not yet replace live-engine rerun proof.

Expected failure conditions:

- Adapter normalization drops or misreads decoy labels.
- Reviewed-proteome accessions drift during import or rollup.

Non-transfer zones:

- Unrepresented proteases or mixed-protease exports.
- Raw-spectrum scoring parity and engine-side calibration behavior.

Obsolescence conditions:

- Search-engine export columns change in a way that the checked fixture no longer reflects current outputs.
- Reference-proteome mapping rules change without a corresponding fixture refresh.

### `dda`: companion generalization package

- package id: `public_companion_package:dda_cross_engine_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_cross_engine_review_package`

Quality blockers:

- no live-engine rerun parity
- generalization remains bounded to two small exported-result packages

Weakness notes:

- The tracked DDA package is still smaller and cleaner than a production multi-run search corpus.
- The package demonstrates protein-rollup drift directly, but it still does not prove live-engine calibration parity.

Fixture realism limits:

- The public package is still a one-run imported-result surface rather than a broader cohort-grade DDA benchmark.
- The package demonstrates cross-engine drift but does not yet replace live-engine rerun proof.

Expected failure conditions:

- Adapter normalization drops or misreads decoy labels.
- Reviewed-proteome accessions drift during import or rollup.

Non-transfer zones:

- Unrepresented proteases or mixed-protease exports.
- Raw-spectrum scoring parity and engine-side calibration behavior.

Obsolescence conditions:

- Search-engine export columns change in a way that the checked fixture no longer reflects current outputs.
- Reference-proteome mapping rules change without a corresponding fixture refresh.

### `dia`: primary flagship package

- package id: `flagship_public_package:dia_library_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package`

Quality blockers:

- no chromatogram-level vendor parity
- library incompleteness and absent-peptide consequences still block broader biological confidence

Weakness notes:

- The public package still does not capture the full instability of production library curation and chromatographic drift.
- Library-conditioned extraction can look more complete than the underlying protein-level support actually is.

Fixture realism limits:

- The checked-in DIA export does not pressure vendor-library churn, chromatography drift, or peptide absence ambiguity at production scale.
- The fixture is library-conditioned and cannot authorize open-ended protein-level absence claims.

Expected failure conditions:

- Transition semantics drift while column names still normalize cleanly.
- Library scope is dropped from the final review surface.

Non-transfer zones:

- Unseen library compositions, vendor-tuned extraction heuristics, and chromatographic drift outside the fixture.
- Protein-level absence claims inferred from library-conditioned missing peptides.

Obsolescence conditions:

- Supported DIA export dialects change without fixture refresh.
- Controlled-vocabulary mappings or library assumptions change materially.

### `dia`: companion generalization package

- package id: `public_companion_package:dia_matrix_shift_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_matrix_shift_review_package`

Quality blockers:

- protein-evidence transfer remains weaker than precursor-level review transfer
- library-conditioned authority still caps the family posture

Weakness notes:

- The public package still does not capture the full instability of production library curation and chromatographic drift.
- Library-conditioned extraction can look more complete than the underlying protein-level support actually is.

Fixture realism limits:

- The checked-in DIA export does not pressure vendor-library churn, chromatography drift, or peptide absence ambiguity at production scale.
- The fixture is library-conditioned and cannot authorize open-ended protein-level absence claims.

Expected failure conditions:

- Transition semantics drift while column names still normalize cleanly.
- Library scope is dropped from the final review surface.

Non-transfer zones:

- Unseen library compositions, vendor-tuned extraction heuristics, and chromatographic drift outside the fixture.
- Protein-level absence claims inferred from library-conditioned missing peptides.

Obsolescence conditions:

- Supported DIA export dialects change without fixture refresh.
- Controlled-vocabulary mappings or library assumptions change materially.

### `lfq`: primary flagship package

- package id: `flagship_public_package:lfq_cohort_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package`

Quality blockers:

- no stronger public truth package for accuracy beyond repeatability
- generalization beyond the current cohort package remains explicitly bounded

Weakness notes:

- The public package still underrepresents the sample heterogeneity and dropout patterns seen in broader production cohorts.
- Protein-level repeatability can obscure peptide-level ambiguity and design-sensitive missingness.

Fixture realism limits:

- The LFQ fixture does not represent broader cohort heterogeneity or severe missing-not-at-random behavior.
- Repeatability under this study shape does not authorize decision-grade abundance claims by itself.

Expected failure conditions:

- Protein rollups remain numerically stable while missingness or contrast semantics drift.
- Design annotations survive import but no longer match the benchmarked comparison.

Non-transfer zones:

- Large heterogeneous cohorts with stronger missing-not-at-random behavior.
- Accuracy claims against external LFQ pipelines or spike-in truth sets.

Obsolescence conditions:

- LFQ design fixtures change in sample structure without metadata refresh.
- Quantification claims expand beyond repeatability into accuracy without new truth evidence.

### `lfq`: companion generalization package

- package id: `public_companion_package:lfq_sparse_contrast_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_sparse_contrast_review_package`

Quality blockers:

- effect-direction confidence weakens under sparser contrast
- family authority remains bounded rather than decision-grade

Weakness notes:

- The public package still underrepresents the sample heterogeneity and dropout patterns seen in broader production cohorts.
- Protein-level repeatability can obscure peptide-level ambiguity and design-sensitive missingness.

Fixture realism limits:

- The LFQ fixture does not represent broader cohort heterogeneity or severe missing-not-at-random behavior.
- Repeatability under this study shape does not authorize decision-grade abundance claims by itself.

Expected failure conditions:

- Protein rollups remain numerically stable while missingness or contrast semantics drift.
- Design annotations survive import but no longer match the benchmarked comparison.

Non-transfer zones:

- Large heterogeneous cohorts with stronger missing-not-at-random behavior.
- Accuracy claims against external LFQ pipelines or spike-in truth sets.

Obsolescence conditions:

- LFQ design fixtures change in sample structure without metadata refresh.
- Quantification claims expand beyond repeatability into accuracy without new truth evidence.

### `multiplex`: primary flagship package

- package id: `flagship_public_package:multiplex_tmtpro_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package`

Quality blockers:

- no multiplex lab packet or outsider review packet family
- multiplex authority is intentionally kept out of the outsider-facing flagship set

Weakness notes:

- The public package surface is still narrower than production multiplex cohorts with more severe missing-channel and interference behavior.
- Channel stability can look stronger than the underlying protein-level certainty actually is.

Fixture realism limits:

- The multiplex fixture does not exercise the strongest carrier overload, interference, or unbalanced cohort behavior seen in production.
- Reporter stability under this fixture does not authorize label-free-style decision claims.

Expected failure conditions:

- Reporter-channel assignments drift or collapse during quantification rollup.
- Channel-level caveats disappear from the final interpretation surface.

Non-transfer zones:

- Severe interference, carrier overload, and vendor-specific multiplex tuning outside the bundled fixture.
- Claims that reporter summaries are interchangeable with label-free abundance truth.

Obsolescence conditions:

- Multiplex channel mappings or fixture design change without metadata refresh.
- Supported multiplex chemistry families change without benchmark scope review.

### `multiplex`: companion generalization package

- package id: `public_companion_package:multiplex_channel_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_channel_stress_review_package`

Quality blockers:

- multiplex still lacks outsider review and lab consequence posture
- public release language remains internal-support only even with a second package

Weakness notes:

- The public package surface is still narrower than production multiplex cohorts with more severe missing-channel and interference behavior.
- Channel stability can look stronger than the underlying protein-level certainty actually is.

Fixture realism limits:

- The multiplex fixture does not exercise the strongest carrier overload, interference, or unbalanced cohort behavior seen in production.
- Reporter stability under this fixture does not authorize label-free-style decision claims.

Expected failure conditions:

- Reporter-channel assignments drift or collapse during quantification rollup.
- Channel-level caveats disappear from the final interpretation surface.

Non-transfer zones:

- Severe interference, carrier overload, and vendor-specific multiplex tuning outside the bundled fixture.
- Claims that reporter summaries are interchangeable with label-free abundance truth.

Obsolescence conditions:

- Multiplex channel mappings or fixture design change without metadata refresh.
- Supported multiplex chemistry families change without benchmark scope review.

### `ptm`: primary flagship package

- package id: `flagship_public_package:ptm_localization_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package`

Quality blockers:

- occupancy and regulatory interpretation still remain narrower than localization evidence
- PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning

Weakness notes:

- Localization confidence can still hide uncertainty about biological relevance and occupancy magnitude.
- The public package is still phosphorylation-oriented and does not generalize to every PTM family equally well under broader production PTM diversity.

Fixture realism limits:

- The fixture emphasizes phosphorylation localization and does not represent full PTM family diversity.
- The dataset is too tidy to authorize occupancy or broad regulatory storytelling on its own.

Expected failure conditions:

- Localized and ambiguous site groups are collapsed into one accepted site claim.
- PTM concept identifiers resolve while localization confidence is discarded.

Non-transfer zones:

- Stoichiometric occupancy and broad regulatory claims.
- PTM families that are not represented by the phosphorylation-oriented fixture.

Obsolescence conditions:

- PTM localization conventions change without a fixture refresh.
- Supported PTM families broaden or narrow without updating the benchmark scope.

### `ptm`: companion generalization package

- package id: `public_companion_package:ptm_ambiguity_stress_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_ambiguity_stress_review_package`

Quality blockers:

- targetability weakens materially under ambiguity stress
- family authority remains bounded rather than decision-grade

Weakness notes:

- Localization confidence can still hide uncertainty about biological relevance and occupancy magnitude.
- The public package is still phosphorylation-oriented and does not generalize to every PTM family equally well under broader production PTM diversity.

Fixture realism limits:

- The fixture emphasizes phosphorylation localization and does not represent full PTM family diversity.
- The dataset is too tidy to authorize occupancy or broad regulatory storytelling on its own.

Expected failure conditions:

- Localized and ambiguous site groups are collapsed into one accepted site claim.
- PTM concept identifiers resolve while localization confidence is discarded.

Non-transfer zones:

- Stoichiometric occupancy and broad regulatory claims.
- PTM families that are not represented by the phosphorylation-oriented fixture.

Obsolescence conditions:

- PTM localization conventions change without a fixture refresh.
- Supported PTM families broaden or narrow without updating the benchmark scope.

### `targeted`: primary flagship package

- package id: `flagship_public_package:targeted_transition_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package`

Quality blockers:

- vendor-parity and calibration-clean authority are still outside the current proof boundary
- targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty

Weakness notes:

- The public package evidence is still operationally tidy compared with noisier targeted production runs and carryover scenarios.
- Transition retention is easier to prove than protein-specific interpretability in shared-peptide settings.

Fixture realism limits:

- The targeted fixture does not cover vendor-specific chromatogram quirks, calibration standards, or messy carryover behavior.
- Transition retention under this fixture does not authorize direct protein certainty claims.

Expected failure conditions:

- Transition QC stays numerically stable while rollup removes protein-inference caution.
- Chromatogram warnings are flattened into a clean targeted-support claim.

Non-transfer zones:

- Vendor-specific chromatogram behavior, calibration standards, and transition-interference edge cases outside the bundled fixture.
- Claims that targeted QC alone resolves shared-peptide ambiguity or confirms protein truth.

Obsolescence conditions:

- Targeted fixture schema changes without updated transition-level metadata.
- Targeted support claims expand into vendor or calibration parity without new benchmark evidence.

### `targeted`: companion generalization package

- package id: `public_companion_package:targeted_carryover_review_package`
- package root: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_carryover_review_package`

Quality blockers:

- stronger carryover pressure weakens promotion confidence
- family authority remains bounded by calibration and vendor-parity limits

Weakness notes:

- The public package evidence is still operationally tidy compared with noisier targeted production runs and carryover scenarios.
- Transition retention is easier to prove than protein-specific interpretability in shared-peptide settings.

Fixture realism limits:

- The targeted fixture does not cover vendor-specific chromatogram quirks, calibration standards, or messy carryover behavior.
- Transition retention under this fixture does not authorize direct protein certainty claims.

Expected failure conditions:

- Transition QC stays numerically stable while rollup removes protein-inference caution.
- Chromatogram warnings are flattened into a clean targeted-support claim.

Non-transfer zones:

- Vendor-specific chromatogram behavior, calibration standards, and transition-interference edge cases outside the bundled fixture.
- Claims that targeted QC alone resolves shared-peptide ambiguity or confirms protein truth.

Obsolescence conditions:

- Targeted fixture schema changes without updated transition-level metadata.
- Targeted support claims expand into vendor or calibration parity without new benchmark evidence.
