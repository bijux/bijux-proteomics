# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.quantification import (
    PeptideMatrixGroupingMode,
    ProteinSharedPeptidePolicy,
    ProteinMatrixTargetKind,
    QuantRollupMethod,
    build_peptide_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_features,
    build_protein_intensity_matrix_from_peptides,
    build_protein_intensity_matrix_from_psms,
    parse_ms1_feature_table,
    render_protein_peptide_contribution_tsv,
    render_protein_intensity_matrix_summary_tsv,
    render_protein_intensity_matrix_tsv,
    render_protein_intensity_missingness_mask_tsv,
    render_protein_intensity_missingness_tsv,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_protein_intensity_matrix_from_features_supports_sum_median_and_top_n() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_matrix_features.tsv"))

    summed = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    median = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.MEDIAN,
    )
    top_n = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    sum_lookup = {
        (row.entity_id, value.sample_id): value.abundance
        for row in summed.rows
        for value in row.values
    }
    median_lookup = {
        (row.entity_id, value.sample_id): value.abundance
        for row in median.rows
        for value in row.values
    }
    top_lookup = {
        (row.entity_id, value.sample_id): value.abundance
        for row in top_n.rows
        for value in row.values
    }

    assert sum_lookup[("P1", "S1")] == 1900.0
    assert median_lookup[("P1", "S1")] == 600.0
    assert top_lookup[("P1", "S1")] == 1600.0
    assert sum_lookup[("P2", "S1")] == 800.0
    assert top_lookup[("P2", "S1")] == 800.0


def test_protein_intensity_matrix_supports_unique_only_and_reports_peptide_counts() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("protein_matrix_features.tsv"))
    matrix = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        unique_only=True,
    )

    assert matrix.summary.unique_only is True
    p1 = next(row for row in matrix.rows if row.entity_id == "P1")
    p2 = next(row for row in matrix.rows if row.entity_id == "P2")
    p1_lookup = {value.sample_id: value for value in p1.values}
    p2_lookup = {value.sample_id: value for value in p2.values}

    assert p1.peptide_count == 2
    assert p1.unique_peptide_count == 2
    assert p1.shared_peptide_count == 0
    assert p1_lookup["S1"].abundance == 1600.0
    assert p2.peptide_count == 1
    assert p2_lookup["S2"].abundance is None
    assert p2_lookup["S2"].missing_value_kind.value == "missing_not_observed"
    assert all(
        value.shared_peptide_policy is ProteinSharedPeptidePolicy.UNIQUE_ONLY
        for row in matrix.rows
        for value in row.values
    )

    shared_entries = [
        entry
        for entry in matrix.peptide_contribution_entries
        if entry.entity_id == "P1" and entry.peptide_id == "SHAREDK"
    ]
    assert len(shared_entries) == 2
    assert all(entry.shared_peptide is True for entry in shared_entries)
    assert all(
        entry.eligible_under_shared_peptide_policy is False for entry in shared_entries
    )
    assert all(entry.included_by_policy is False for entry in shared_entries)
    assert all(
        entry.shared_peptide_policy is ProteinSharedPeptidePolicy.UNIQUE_ONLY
        for entry in shared_entries
    )


def test_protein_intensity_matrix_decomposes_per_value_peptide_contributors() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_matrix_features.tsv"))
    matrix = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )

    entry_lookup = {
        (entry.entity_id, entry.sample_id, entry.peptide_id): entry
        for entry in matrix.peptide_contribution_entries
    }
    top_entry = entry_lookup[("P1", "S1", "PEPAAK")]
    second_entry = entry_lookup[("P1", "S1", "PEPMTK")]
    excluded_entry = entry_lookup[("P1", "S1", "SHAREDK")]
    p1_s1 = next(
        value
        for row in matrix.rows
        if row.entity_id == "P1"
        for value in row.values
        if value.sample_id == "S1"
    )

    assert p1_s1.abundance == 1600.0
    assert p1_s1.contributing_peptide_count == 2
    assert top_entry.protein_value_abundance == 1600.0
    assert top_entry.abundance_rank == 1
    assert top_entry.included_abundance_fraction == 0.625
    assert top_entry.abundance_to_protein_value_ratio == 0.625
    assert second_entry.abundance_rank == 2
    assert second_entry.included_abundance_fraction == 0.375
    assert excluded_entry.eligible_under_shared_peptide_policy is True
    assert excluded_entry.included_by_policy is False
    assert excluded_entry.abundance_rank == 3
    assert excluded_entry.included_abundance_fraction is None
    assert excluded_entry.abundance_to_protein_value_ratio == 0.1875


def test_protein_intensity_matrix_can_target_exact_protein_groups() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_matrix_features.tsv"))
    matrix = build_protein_intensity_matrix_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN_GROUP,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert {row.entity_id for row in matrix.rows} == {"P1", "P1;P2", "P2"}
    shared = next(row for row in matrix.rows if row.entity_id == "P1;P2")
    lookup = {value.sample_id: value for value in shared.values}
    assert shared.peptide_count == 1
    assert shared.shared_peptide_count == 1
    assert shared.unique_peptide_count == 0
    assert lookup["S1"].abundance == 300.0
    assert lookup["S2"].abundance == 450.0


def test_protein_intensity_matrix_from_psms_and_renderers_preserve_skips_and_ledgers() -> (
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
    matrix = build_protein_intensity_matrix_from_psms(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    summary_tsv = render_protein_intensity_matrix_summary_tsv(matrix)
    matrix_tsv = render_protein_intensity_matrix_tsv(matrix)
    missingness_tsv = render_protein_intensity_missingness_tsv(matrix)
    missingness_mask_tsv = render_protein_intensity_missingness_mask_tsv(matrix)
    contribution_tsv = render_protein_peptide_contribution_tsv(matrix)

    assert matrix.summary.protein_row_count == 1
    assert matrix.summary.missing_cell_count == 0
    assert "psm\tmodified_peptide\tprotein\tfalse\tsum\tfalse" in summary_tsv
    assert (
        "entity_id\ttarget_kind\tprotein_refs\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tcontributing_peptides\tR1\tR2"
        in matrix_tsv
    )
    assert (
        "P001\tprotein\tP001\t2\t2\t0\tPEMTIDE;PEM[Oxidation]TIDE\t1900\t1900"
        in matrix_tsv
    )
    assert "R1\t1\t0\t0\t0" in missingness_tsv
    assert (
        "sample_id\tobserved_count\tzero_count\tnot_observed_count\tfiltered_count\timputed_count\tcensored_count\texcluded_count\tnot_applicable_count"
        in missingness_tsv
    )
    assert (
        "entity_id\ttarget_kind\tprotein_refs\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tcontributing_peptides\tR1\tR2"
        in missingness_mask_tsv
    )
    assert (
        "P001\tprotein\tP001\t2\t2\t0\tPEMTIDE;PEM[Oxidation]TIDE\tobserved\tobserved"
        in missingness_mask_tsv
    )
    assert (
        "entity_id\ttarget_kind\tsample_id\tpeptide_id\tpeptide_sequence\tprotein_refs\tabundance\tmissing_value_kind\tshared_peptide\teligible_under_shared_peptide_policy\tincluded_by_policy\tprotein_value_abundance\tabundance_rank\tincluded_abundance_fraction\tabundance_to_protein_value_ratio\tshared_peptide_policy"
        in contribution_tsv
    )
    assert (
        "P001\tprotein\tR1\tPEMTIDE\tPEMTIDE\tP001\t1900\tobserved\tfalse\ttrue\ttrue\t1900\t1\t1.000000\t1.000000\tall_peptides"
        in contribution_tsv
    )


def test_protein_intensity_matrix_accepts_canonical_peptide_matrix_input() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_matrix_features.tsv"))
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    ).to_quant_matrix()

    matrix = build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    assert matrix.quant_matrix is not None
    assert matrix.quant_matrix.entity_kind.value == "protein"
    assert any(
        support_count >= 1
        for row in matrix.quant_matrix.support_counts
        for support_count in row
    )
