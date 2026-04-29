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

## Python API

```python
from pathlib import Path

from bijux_proteomics import (
    apply_benjamini_hochberg,
    build_batch_effect_advisory,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_replicate_correlation_report,
    normalize_label_free_table,
    NormalizationMethod,
    parse_experimental_design_table,
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

## Current limits

- differential abundance is intentionally limited to two-condition comparisons
- the statistical test is a basic Welch-style test, not a full limma/DEqMS-like
  model
- batch and replicate surfaces are advisory and do not change quant values
- TMT/DIA quantification is not part of this slice
