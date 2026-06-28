# Quantification Workflows

`bijux-proteomics-core` now carries a first-class label-free quantification
surface for MS1 feature tables.

This slice is intentionally focused:

- `ENFORCED`:
  - MS1 feature parsing
  - peptide and protein rollups
  - missing-value state preservation
  - TIC, median, and quantile normalization
  - two-condition differential abundance with Benjamini-Hochberg correction
- `ADVISORY`:
  - batch effect reporting
  - replicate correlation reporting

It also now carries one owned peptide-intensity matrix surface that can start
from either precursor or feature tables or intensity-bearing PSM tables when
run identity is explicit.

Protein-level matrix construction is now explicit too, rather than being
treated as an implicit follow-on spreadsheet collapse.

It now also carries one owned MaxLFQ-like protein surface that preserves
pairwise peptide ratios across samples instead of stopping at direct protein
rollup.

## Input contract

The quantification parser expects a delimited table with these canonical
columns:

- `sample_id`
- `feature_id`
- `peptide`
- `intensity`
- `proteins`

Optional columns:

- `charge`
- `mz`
- `retention_time_seconds`
- `missing_reason`

`missing_reason=filtered` is preserved as a distinct filtered state instead of
being collapsed into generic missingness. Explicit zero intensity is preserved
separately from not-observed cells.

## Design-table contract

Quantification reports can join an experimental design table with these stable
fields:

- `sample_id`
- `condition`
- `replicate`
- `fraction`
- `spectra_file`

Optional metadata used by the quant workflows:

- `batch`
- `instrument`
- `search_engine`

Batch advisories prefer the explicit `batch` field and fall back to
`instrument` when no batch column is available.

## Boundary notes

- `bijux_proteomics.quantification` is the reader-facing facade for stable
  workflows and compatibility wrappers
- `bijux_proteomics.quantification.contracts` is the curated public contract
  facade
- internal core code should import owner modules such as `design`,
  `differential`, `input_models`, `label_based`, `matrix_building`,
  `matrix_models`, `missingness`, `normalization_imputation`,
  `protein_rollup`, and `study_qc` directly instead of routing through the
  root contracts barrel
- underscore-prefixed helpers are owner-local implementation details, not
  public contract surface

## Python API

```python
from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    PeptideMatrixGroupingMode,
    ProteinMatrixTargetKind,
    apply_benjamini_hochberg,
    build_batch_effect_advisory,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_protein_lfq_report_from_psms,
    build_peptide_intensity_matrix_from_psms,
    build_protein_intensity_matrix_from_peptides,
    build_replicate_correlation_report,
    normalize_label_free_table,
    NormalizationMethod,
    parse_ms1_feature_table,
    QuantEntityLevel,
    QuantRollupMethod,
)

feature_report = parse_ms1_feature_table(Path("ms1_features.tsv"))
design_report = parse_experimental_design_table(Path("quant.design.tsv"))

protein_table = build_label_free_intensity_table(
    feature_report.accepted_records,
    entity_level=QuantEntityLevel.PROTEIN,
    aggregation_method=QuantRollupMethod.TOP_N,
    top_n=2,
)
normalized = normalize_label_free_table(
    protein_table,
    method=NormalizationMethod.MEDIAN,
)

batch_report = build_batch_effect_advisory(
    normalized,
    design_report.accepted_entries,
)
replicate_report = build_replicate_correlation_report(
    normalized,
    design_report.accepted_entries,
)
differential = apply_benjamini_hochberg(
    build_differential_abundance_report(
        normalized,
        design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )
)

psm_report = parse_psm_tsv(
    Path("search_with_intensity.tsv"),
    mapping=SearchResultColumnMapping(
        run_id="run_id",
        spectrum_id="spectrum_id",
        peptide="peptide",
        modified_peptide="modified_peptide",
        charge="charge",
        score="score",
        intensity="intensity",
        protein_refs="proteins",
    ),
)
peptide_matrix = build_peptide_intensity_matrix_from_psms(
    psm_report.accepted_records,
    grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states=True,
)
protein_matrix = build_protein_intensity_matrix_from_peptides(
    peptide_matrix,
    target_kind=ProteinMatrixTargetKind.PROTEIN,
    unique_only=True,
)
protein_lfq = build_protein_lfq_report_from_psms(
    psm_report.accepted_records,
    grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    target_kind=ProteinMatrixTargetKind.PROTEIN,
    aggregation_method=QuantRollupMethod.SUM,
    minimum_shared_peptides=2,
)
```

## CLI workflow

```bash
bijux-proteomics quantify ms1_features.tsv \
  --design quant.design.tsv \
  --entity-level protein \
  --aggregation top_n \
  --top-n 2 \
  --normalization median \
  --condition-a control \
  --condition-b treatment \
  --report-out quant.report.json
```

The report includes:

- accepted and rejected feature counts
- a stable quantification table
- missing-value summary
- batch advisory report
- replicate correlation report
- differential abundance report with adjusted p-values

For direct peptide-matrix review:

```bash
bijux-proteomics peptide-matrix ms1_features.tsv \
  --input-kind feature \
  --grouping-mode modified_peptide \
  --separate-charge-states \
  --summary-tsv-out peptide-matrix.summary.tsv \
  --matrix-tsv-out peptide-matrix.matrix.tsv \
  --missingness-tsv-out peptide-matrix.missingness.tsv \
  --out peptide-matrix.report.json
```

That matrix surface emits:

- accepted and rejected parser counts from the selected input kind
- explicit grouping mode and charge-separation policy
- a peptide-by-sample abundance matrix with one row per peptide grouping
- a per-sample missingness ledger
- skipped-source counts when PSM rows lack run identity or intensity

For direct protein-matrix review:

```bash
bijux-proteomics protein-matrix ms1_features.tsv \
  --input-kind feature \
  --target-kind protein \
  --aggregation top_n \
  --top-n 2 \
  --unique-peptide-only \
  --summary-tsv-out protein-matrix.summary.tsv \
  --matrix-tsv-out protein-matrix.matrix.tsv \
  --missingness-tsv-out protein-matrix.missingness.tsv \
  --out protein-matrix.report.json
```

That protein-matrix surface emits:

- explicit protein versus protein-group targeting
- named sum, median, or top-`n` peptide rollup policy
- optional unique-peptide-only rollup
- peptide count plus unique/shared peptide burden per protein row
- a protein-by-sample abundance matrix and a per-sample missingness ledger

For direct MaxLFQ-like review:

```bash
bijux-proteomics protein-lfq search_with_intensity.tsv \
  --input-kind psm \
  --grouping-mode modified_peptide \
  --target-kind protein \
  --aggregation sum \
  --minimum-shared-peptides 2 \
  --summary-tsv-out protein-lfq.summary.tsv \
  --matrix-tsv-out protein-lfq.matrix.tsv \
  --pairwise-tsv-out protein-lfq.pairwise.tsv \
  --missingness-tsv-out protein-lfq.missingness.tsv \
  --out protein-lfq.report.json
```

That protein-LFQ surface emits:

- explicit peptide grouping, charge policy, and pre-LFQ aggregation policy
- pairwise sample-ratio ledgers per protein or exact protein group
- component-aware least-squares LFQ values across the observed sample graph
- explicit disconnected-component visibility when missing peptides prevent one
  fully connected sample network
- a protein-by-sample LFQ matrix together with summary and missingness ledgers

## Current limits

- differential abundance is intentionally limited to two-condition comparisons
- the statistical test is a basic Welch-style test, not a full limma/DEqMS-like
  model
- batch and replicate surfaces are advisory and do not change quant values
- TMT/DIA quantification is not part of this slice
- the current protein-LFQ surface is intentionally MaxLFQ-like rather than a
  claim of byte-for-byte parity with external tools
- disconnected sample components are reported explicitly instead of being
  forced into one synthetic fully observed profile
- the current PSM matrix path requires intensity-bearing rows and does not infer
  missing abundance from score-only search evidence
- protein-group rollup is intentionally exact-membership based at this stage; it
  does not yet claim later MaxLFQ-like cross-sample reconciliation
