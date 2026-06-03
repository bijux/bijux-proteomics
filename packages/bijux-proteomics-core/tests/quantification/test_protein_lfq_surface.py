# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math
from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.quantification import (
    PeptideMatrixGroupingMode,
    ProteinMatrixTargetKind,
    QuantRollupMethod,
    build_peptide_intensity_matrix_from_features,
    build_protein_lfq_report_from_features,
    build_protein_lfq_report_from_peptides,
    build_protein_lfq_report_from_psms,
    parse_ms1_feature_table,
    render_protein_lfq_disconnected_components_tsv,
    render_protein_lfq_matrix_tsv,
    render_protein_lfq_missingness_mask_tsv,
    render_protein_lfq_missingness_tsv,
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_lfq_summary_tsv,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_protein_lfq_from_features_recovers_pairwise_ratios_and_profile_order() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_lfq_features.tsv"))
    lfq = build_protein_lfq_report_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )

    assert lfq.summary.protein_row_count == 2
    assert lfq.summary.fully_connected_row_count == 1
    assert lfq.summary.disconnected_row_count == 1
    assert lfq.aggregation_method is QuantRollupMethod.SUM

    p1 = next(row for row in lfq.rows if row.entity_id == "P1")
    assert p1.fully_connected is True
    assert p1.connected_component_count == 1
    assert p1.pairwise_ratio_count == 3

    ratio_lookup = {
        (entry.sample_a, entry.sample_b): entry.median_log2_ratio
        for entry in p1.pairwise_ratios
    }
    assert math.isclose(ratio_lookup[("S1", "S2")], 1.0, abs_tol=1e-6)
    assert math.isclose(ratio_lookup[("S1", "S3")], -1.0, abs_tol=1e-6)
    assert math.isclose(ratio_lookup[("S2", "S3")], -2.0, abs_tol=1e-6)

    value_lookup = {value.sample_id: value for value in p1.values}
    assert value_lookup["S2"].abundance is not None
    assert value_lookup["S1"].abundance is not None
    assert value_lookup["S3"].abundance is not None
    assert value_lookup["S2"].abundance > value_lookup["S1"].abundance
    assert value_lookup["S1"].abundance > value_lookup["S3"].abundance
    assert math.isclose(
        value_lookup["S2"].abundance / value_lookup["S1"].abundance,
        2.0,
        rel_tol=1e-6,
    )
    assert math.isclose(
        value_lookup["S3"].abundance / value_lookup["S1"].abundance,
        0.5,
        rel_tol=1e-6,
    )


def test_protein_lfq_handles_disconnected_missing_peptides_with_component_status() -> (
    None
):
    report = parse_ms1_feature_table(_quant_fixture("protein_lfq_features.tsv"))
    lfq = build_protein_lfq_report_from_features(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )

    p2 = next(row for row in lfq.rows if row.entity_id == "P2")
    assert p2.fully_connected is False
    assert p2.connected_component_count == 2
    assert p2.pairwise_ratio_count == 1
    assert lfq.summary.disconnected_component_entry_count == 2

    value_lookup = {value.sample_id: value for value in p2.values}
    assert value_lookup["S1"].component_id == 1
    assert value_lookup["S2"].component_id == 1
    assert value_lookup["S3"].component_id == 2
    assert value_lookup["S1"].abundance is not None
    assert value_lookup["S2"].abundance is not None
    assert math.isclose(
        value_lookup["S2"].abundance / value_lookup["S1"].abundance,
        2.0,
        rel_tol=1e-6,
    )
    assert value_lookup["S3"].abundance is not None

    disconnected_components = {
        entry.component_id: entry
        for entry in lfq.disconnected_components
        if entry.entity_id == "P2"
    }
    assert tuple(sorted(disconnected_components)) == (1, 2)
    assert disconnected_components[1].sample_ids == ("S1", "S2")
    assert disconnected_components[1].disconnected_from_sample_ids == ("S3",)
    assert disconnected_components[1].pairwise_ratio_count == 1
    assert disconnected_components[1].contributing_peptides == ("DISCAAK",)
    assert disconnected_components[2].sample_ids == ("S3",)
    assert disconnected_components[2].disconnected_from_sample_ids == ("S1", "S2")
    assert disconnected_components[2].pairwise_ratio_count == 0
    assert disconnected_components[2].contributing_peptides == ("DISCVVK",)


def test_protein_lfq_from_psms_skips_rows_without_run_or_intensity_and_renders_ledgers() -> (
    None
):
    report = parse_psm_tsv(
        _quant_fixture("protein_lfq_psms.tsv"),
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
    lfq = build_protein_lfq_report_from_psms(
        report.accepted_records,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )

    assert lfq.summary.protein_row_count == 1
    p1 = lfq.rows[0]
    assert p1.entity_id == "P1"
    assert p1.pairwise_ratio_count == 3

    summary_tsv = render_protein_lfq_summary_tsv(lfq)
    matrix_tsv = render_protein_lfq_matrix_tsv(lfq)
    pairwise_tsv = render_protein_lfq_pairwise_ratios_tsv(lfq)
    disconnected_tsv = render_protein_lfq_disconnected_components_tsv(lfq)
    missingness_tsv = render_protein_lfq_missingness_tsv(lfq)
    missingness_mask_tsv = render_protein_lfq_missingness_mask_tsv(lfq)

    assert (
        "source_kind\tgrouping_mode\ttarget_kind\tseparate_charge_states\taggregation_method"
        in summary_tsv
    )
    assert "psm\tmodified_peptide\tprotein\tfalse\tsum\tfalse\t1\t" in summary_tsv
    assert (
        "entity_id\ttarget_kind\tprotein_refs\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tpairwise_ratio_count\tconnected_component_count\tcontributing_peptides\tS1\tS2\tS3"
        in matrix_tsv
    )
    assert "P1\tprotein\tP1\t3\t3\t0\t3\t1\tPEPAAK;PEPCCK;PEPVVK\t" in matrix_tsv
    assert (
        "entity_id\ttarget_kind\tsample_a\tsample_b\tshared_peptide_count"
        in pairwise_tsv
    )
    assert "P1\tprotein\tS1\tS2\t2\t1\t2\tPEPAAK;PEPVVK" in pairwise_tsv
    assert (
        "sample_id\tobserved_count\tzero_count\tnot_observed_count\tfiltered_count"
        in missingness_tsv
    )
    assert (
        "sample_id\tobserved_count\tzero_count\tnot_observed_count\tfiltered_count\timputed_count\tcensored_count\texcluded_count\tnot_applicable_count"
        in missingness_tsv
    )
    assert (
        "entity_id\ttarget_kind\tprotein_refs\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tpairwise_ratio_count\tconnected_component_count\tcontributing_peptides\tS1\tS2\tS3"
        in missingness_mask_tsv
    )
    assert (
        "P1\tprotein\tP1\t3\t3\t0\t3\t1\tPEPAAK;PEPCCK;PEPVVK\tobserved\tobserved\tobserved"
        in missingness_mask_tsv
    )
    assert (
        "entity_id\ttarget_kind\tprotein_refs\tcomponent_id\tsample_ids\tdisconnected_from_sample_ids\tsample_count\tpairwise_ratio_count\tcontributing_peptides"
        in disconnected_tsv
    )
    assert disconnected_tsv == (
        "entity_id\ttarget_kind\tprotein_refs\tcomponent_id\tsample_ids\tdisconnected_from_sample_ids\tsample_count\tpairwise_ratio_count\tcontributing_peptides\n"
    )


def test_protein_lfq_accepts_canonical_peptide_matrix_input() -> None:
    report = parse_ms1_feature_table(_quant_fixture("protein_lfq_features.tsv"))
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        report.accepted_records,
        grouping_mode=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    ).to_quant_matrix()

    lfq = build_protein_lfq_report_from_peptides(
        peptide_matrix,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )

    assert lfq.quant_matrix is not None
    assert lfq.quant_matrix.entity_kind.value == "protein"
    assert lfq.quant_matrix.support_counts
