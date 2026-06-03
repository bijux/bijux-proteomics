# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    ImputationMethod,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    QuantValueOrigin,
    build_label_free_intensity_table,
    build_quant_value_provenance_report,
    export_quant_value_provenance_tsv,
    impute_label_free_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
    render_quant_value_provenance_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_quant_value_provenance_report_preserves_selected_and_excluded_support() -> (
    None
):
    records = parse_ms1_feature_table(_fixture("ms1_features.tsv")).accepted_records
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    report = build_quant_value_provenance_report(table)
    row = next(
        row for row in report.rows if row.entity_id == "P001" and row.sample_id == "C1"
    )
    missing_row = next(
        row for row in report.rows if row.entity_id == "P003" and row.sample_id == "C1"
    )

    assert report.summary.row_count == len(table.values)
    assert row.value_origin is QuantValueOrigin.OBSERVED
    assert row.source_feature_ids == ("f001", "f002")
    assert row.source_peptides == ("APEPTIDE", "APEPTIDER")
    assert row.excluded_contributor_ids == ("f005",)
    assert row.exclusion_reason_codes == ("excluded_by_top_n_rollup",)
    assert missing_row.value_origin is QuantValueOrigin.MISSING
    assert missing_row.excluded_contributor_ids == ("f006",)
    assert missing_row.exclusion_reason_codes == ("missing_value_filtered",)


def test_quant_value_provenance_report_marks_imputed_rows_and_renders_tsv(
    tmp_path: Path,
) -> None:
    records = parse_ms1_feature_table(_fixture("ms1_features.tsv")).accepted_records
    design_entries = parse_experimental_design_table(
        _fixture("quant.design.tsv")
    ).accepted_entries
    imputed = impute_label_free_table(
        normalize_label_free_table(
            build_label_free_intensity_table(
                records,
                entity_level=QuantEntityLevel.PROTEIN,
                aggregation_method=QuantRollupMethod.SUM,
            ),
            method=NormalizationMethod.MEDIAN,
        ),
        method=ImputationMethod.GROUP_AWARE_LOW_INTENSITY,
        design_entries=design_entries,
    )

    report = build_quant_value_provenance_report(imputed)
    row = next(
        row for row in report.rows if row.entity_id == "P004" and row.sample_id == "C1"
    )

    assert row.value_origin is QuantValueOrigin.IMPUTED
    assert row.imputation_method is ImputationMethod.GROUP_AWARE_LOW_INTENSITY
    rendered = render_quant_value_provenance_tsv(report)
    assert rendered.startswith("entity_id\tsample_id\tentity_level")
    assert "value_origin" in rendered.splitlines()[0]
    assert "group_aware_low_intensity" in rendered

    output_path = tmp_path / "quant_value_provenance.tsv"
    export_quant_value_provenance_tsv(report, output_path)
    assert output_path.read_text(encoding="utf-8") == rendered
