# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.quantification import (
    PeptideMatrixGroupingMode,
    QuantRollupMethod,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_precursors,
    build_peptide_intensity_matrix_from_psms,
    parse_ms1_feature_table,
    parse_precursor_intensity_table,
    render_peptide_intensity_aggregation_tsv,
    render_peptide_intensity_matrix_summary_tsv,
    render_peptide_intensity_matrix_tsv,
    render_peptide_intensity_missingness_mask_tsv,
    render_peptide_intensity_missingness_tsv,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_peptide_intensity_matrix_from_features_preserves_grouping_charge_and_missingness() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("peptide_matrix_features.tsv"))
    matrix = build_peptide_intensity_matrix_from_features(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.PEPTIDE_SEQUENCE,
        separate_charge_states=False,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert matrix.summary.accepted_source_record_count == 7
    assert matrix.summary.sample_count == 2
    assert matrix.summary.peptide_row_count == 2
    assert matrix.summary.filtered_cell_count == 0
    assert matrix.summary.missing_cell_count == 2

    peptide_row = next(row for row in matrix.rows if row.entity_id == "PEMTIDE")
    assert peptide_row.modified_peptides == ("PEMTIDE", "PEM[Oxidation]TIDE")
    assert peptide_row.charge_states == (2, 3)
    value_lookup = {value.sample_id: value for value in peptide_row.values}
    assert value_lookup["S1"].abundance == 2400.0
    assert value_lookup["S2"].abundance == 1200.0

    miss_row = next(row for row in matrix.rows if row.entity_id == "MISSPEP")
    assert miss_row.values[1].missing_value_kind.value == "missing_not_observed"


def test_peptide_intensity_matrix_from_features_can_split_modified_charge_rows() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("peptide_matrix_features.tsv"))
    matrix = build_peptide_intensity_matrix_from_features(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        separate_charge_states=True,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert {row.entity_id for row in matrix.rows} == {
        "MISSPEP/z2",
        "PEMTIDE/z2",
        "PEMTIDE/z3",
        "PEM[Oxidation]TIDE/z2",
    }
    oxidized = next(
        row for row in matrix.rows if row.entity_id == "PEM[Oxidation]TIDE/z2"
    )
    oxidized_lookup = {value.sample_id: value for value in oxidized.values}
    assert oxidized_lookup["S1"].abundance == 400.0
    assert oxidized_lookup["S2"].missing_value_kind.value == "filtered"


def test_peptide_intensity_matrix_from_psms_skips_rows_without_run_or_intensity() -> (
    None
):
    report = parse_psm_tsv(
        _quant_fixture("peptide_matrix_psms.tsv"),
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
    matrix = build_peptide_intensity_matrix_from_psms(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        separate_charge_states=False,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert matrix.summary.accepted_source_record_count == 5
    assert matrix.summary.skipped_source_record_count == 2
    assert matrix.summary.sample_count == 2
    assert matrix.summary.peptide_row_count == 2
    peptide_row = next(row for row in matrix.rows if row.entity_id == "PEMTIDE")
    lookup = {value.sample_id: value for value in peptide_row.values}
    assert lookup["R1"].abundance == 1900.0
    assert lookup["R2"].abundance == 1200.0
    assert matrix.summary.missing_cell_count == 1


def test_peptide_intensity_matrix_from_precursors_exposes_aggregation_policy() -> None:
    report = parse_precursor_intensity_table(
        _quant_fixture("peptide_matrix_precursors.tsv")
    )
    matrix = build_peptide_intensity_matrix_from_precursors(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        separate_charge_states=False,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    assert matrix.source_kind.value == "precursor"
    assert matrix.summary.accepted_source_record_count == 7
    assert matrix.summary.sample_count == 3
    assert matrix.summary.peptide_row_count == 2
    assert matrix.summary.filtered_cell_count == 1
    assert matrix.summary.missing_cell_count == 1

    peptide_row = next(row for row in matrix.rows if row.entity_id == "PEPTIDE")
    peptide_lookup = {value.sample_id: value for value in peptide_row.values}
    assert peptide_lookup["S1"].abundance == 700.0
    assert peptide_lookup["S1"].source_record_count == 2

    filtered_row = next(
        row for row in matrix.rows if row.entity_id == "M[Oxidation]PEPTIDE"
    )
    filtered_lookup = {value.sample_id: value for value in filtered_row.values}
    assert filtered_lookup["S1"].abundance == 150.0
    assert filtered_lookup["S2"].missing_value_kind.value == "filtered"
    assert filtered_lookup["S3"].missing_value_kind.value == "missing_not_observed"

    aggregation_entry = next(
        entry
        for entry in matrix.aggregation_entries
        if entry.entity_id == "PEPTIDE" and entry.sample_id == "S1"
    )
    assert aggregation_entry.aggregation_method.value == "top_n"
    assert aggregation_entry.source_record_ids == ("ppq001", "ppq002")
    assert aggregation_entry.source_abundances == (500.0, 200.0)
    assert aggregation_entry.aggregated_abundance == 700.0
    assert aggregation_entry.quantified_record_count == 2
    assert aggregation_entry.source_record_count == 2


def test_peptide_intensity_matrix_renderers_emit_summary_matrix_and_missingness_ledgers() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("peptide_matrix_features.tsv"))
    matrix = build_peptide_intensity_matrix_from_features(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        separate_charge_states=True,
        aggregation_method=QuantRollupMethod.SUM,
    )

    summary_tsv = render_peptide_intensity_matrix_summary_tsv(matrix)
    matrix_tsv = render_peptide_intensity_matrix_tsv(matrix)
    missingness_tsv = render_peptide_intensity_missingness_tsv(matrix)

    assert "grouping_mode\t" in summary_tsv
    assert "feature\tmodified_peptide\ttrue\tsum" in summary_tsv
    assert (
        "entity_id\tpeptide_sequence\tmodified_peptides\tcharge_states\tprotein_refs\tS1\tS2"
        in matrix_tsv
    )
    assert "PEMTIDE/z2\tPEMTIDE\tPEMTIDE\t2\tP001\t1200\t1200" in matrix_tsv
    assert (
        "sample_id\tobserved_count\tzero_count\tnot_observed_count\tfiltered_count"
        in missingness_tsv
    )
    assert "S2\t1\t0\t2\t1" in missingness_tsv


def test_peptide_intensity_matrix_renderers_emit_missingness_mask_and_aggregation_ledgers() -> (
    None
):
    report = parse_precursor_intensity_table(
        _quant_fixture("peptide_matrix_precursors.tsv")
    )
    matrix = build_peptide_intensity_matrix_from_precursors(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        separate_charge_states=False,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    missingness_mask_tsv = render_peptide_intensity_missingness_mask_tsv(matrix)
    aggregation_tsv = render_peptide_intensity_aggregation_tsv(matrix)

    assert (
        "entity_id\tpeptide_sequence\tmodified_peptides\tcharge_states\tprotein_refs\tS1\tS2\tS3"
        in missingness_mask_tsv
    )
    assert (
        "M[Oxidation]PEPTIDE\tMPEPTIDE\tM[Oxidation]PEPTIDE\t2\tP002\tobserved\tfiltered\tmissing_not_observed"
        in missingness_mask_tsv
    )
    assert (
        "entity_id\tsample_id\tpeptide_sequence\tmodified_peptides\tcharge_states\tprotein_refs\taggregation_method"
        in aggregation_tsv
    )
    assert (
        "PEPTIDE\tS1\tPEPTIDE\tPEPTIDE\t2\tP001\ttop_n\tppq001;ppq002\t2\t2\t2\t0\t0\t0\t500;200\t700\tobserved"
        in aggregation_tsv
    )
