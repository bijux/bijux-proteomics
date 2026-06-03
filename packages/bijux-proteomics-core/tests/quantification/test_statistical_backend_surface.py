# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_limma_compatible_quant_package,
    build_msstats_compatible_input_report,
    build_statistical_backend_validation_report,
    parse_limma_result_table,
    parse_ms1_feature_table,
    parse_msstats_result_table,
    render_limma_assay_matrix_tsv,
    render_limma_contrast_matrix_tsv,
    render_limma_design_matrix_tsv,
    render_limma_sample_annotations_tsv,
    render_msstats_compatible_input_tsv,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def _table_and_design():
    feature_report = parse_ms1_feature_table(_quant_fixture("ms1_features.tsv"))
    design_report = parse_experimental_design_table(_quant_fixture("quant.design.tsv"))
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return feature_report.accepted_records, table, design_report.accepted_entries


def test_build_limma_compatible_quant_package_renders_assay_design_and_contrasts() -> (
    None
):
    _, table, design = _table_and_design()
    package = build_limma_compatible_quant_package(table, design)

    assay_tsv = render_limma_assay_matrix_tsv(package)
    sample_tsv = render_limma_sample_annotations_tsv(package)
    design_tsv = render_limma_design_matrix_tsv(package)
    contrast_tsv = render_limma_contrast_matrix_tsv(package)

    assert package.design_matrix_report.contrasts
    assert assay_tsv.startswith("entity_id\tC1\tC2\tT1\tT2")
    assert "P001" in assay_tsv
    assert sample_tsv.startswith("sample_id\tcondition\tbatch\tpair_id")
    assert "C1\tcontrol\tbatch-a" in sample_tsv
    assert design_tsv.startswith("sample_id\tcondition\tbatch\tpair_id")
    assert "condition[treatment]" in design_tsv
    assert contrast_tsv.startswith("coefficient_name\tcontrol_vs_treatment")
    assert "condition[treatment]\t-1" in contrast_tsv


def test_build_msstats_compatible_input_report_preserves_observed_feature_rows() -> (
    None
):
    records, _, design = _table_and_design()
    report = build_msstats_compatible_input_report(records, design)
    tsv = render_msstats_compatible_input_tsv(report)

    assert report.row_count > 0
    assert report.skipped_feature_count > 0
    assert tsv.startswith(
        "ProteinName\tPeptideSequence\tPrecursorCharge\tCondition\tBioReplicate"
    )
    assert "P001\tAPEPTIDE\t2\tcontrol\tC1\tc1" in tsv


def test_build_msstats_compatible_input_report_allows_missing_charge() -> None:
    records, _, design = _table_and_design()
    charge_optional_records = tuple(
        record.model_copy(update={"charge": None})
        if record.feature_id == "f001"
        else record
        for record in records
    )

    report = build_msstats_compatible_input_report(charge_optional_records, design)
    tsv = render_msstats_compatible_input_tsv(report)

    assert report.row_count > 0
    assert report.skipped_feature_count > 0
    assert "P001\tAPEPTIDE\t\tcontrol\tC1\tc1" in tsv


def test_parse_backend_results_and_validate_against_native_differential_surface() -> (
    None
):
    _, table, design = _table_and_design()
    native_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            table,
            design,
            condition_a="control",
            condition_b="treatment",
        )
    )

    limma_import = parse_limma_result_table(
        _quant_fixture("limma_results.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    msstats_import = parse_msstats_result_table(
        _quant_fixture("msstats_results.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    limma_validation = build_statistical_backend_validation_report(
        limma_import,
        native_report,
    )
    msstats_validation = build_statistical_backend_validation_report(
        msstats_import,
        native_report,
    )

    assert limma_import.row_count == 2
    assert msstats_import.row_count == 2
    assert limma_validation.matched_row_count == 2
    assert limma_validation.directionally_concordant_count == 2
    assert msstats_validation.matched_row_count == 2
    assert msstats_validation.directionally_concordant_count == 2
    assert limma_validation.mean_absolute_log2_fold_change_delta is not None
    assert msstats_validation.mean_absolute_log2_fold_change_delta is not None
