# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_diann_peptide_matrix_report,
    build_diann_protein_matrix_report,
    render_dia_peptide_missingness_tsv,
    render_dia_peptide_matrix_summary_tsv,
    render_dia_peptide_q_value_matrix_tsv,
    render_dia_peptide_quantity_matrix_tsv,
    render_dia_protein_missingness_tsv,
    render_dia_protein_matrix_summary_tsv,
    render_dia_protein_q_value_matrix_tsv,
    render_dia_protein_quantity_matrix_tsv,
    render_dia_protein_rollup_evidence_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_build_diann_peptide_matrix_report_applies_precursor_filters() -> None:
    report = build_diann_peptide_matrix_report(
        _bundle_root() / "diann_report.tsv",
        include_decoys=False,
        max_q_value=0.003,
        rollup_method=DiaPeptideRollupMethod.MAX,
    )

    assert report.summary.peptide_row_count == 1
    assert report.summary.observed_cell_count == 2
    assert report.rows[0].peptide_key == "PESTIDE|PG001"
    assert report.rows[0].values[0].abundance == 1250000.0
    assert report.rows[0].values[1].q_value == 0.0024


def test_render_dia_peptide_matrix_exports() -> None:
    report = build_diann_peptide_matrix_report(_bundle_root() / "diann_report.tsv")

    summary_tsv = render_dia_peptide_matrix_summary_tsv(report)
    quantity_tsv = render_dia_peptide_quantity_matrix_tsv(report)
    missingness_tsv = render_dia_peptide_missingness_tsv(report)
    q_value_tsv = render_dia_peptide_q_value_matrix_tsv(report)

    assert summary_tsv.startswith(
        "source_name\trollup_method\tsample_count\tpeptide_row_count"
    )
    assert "DIA-NN\tmax\t2\t2\t3\t1\t1\t" in summary_tsv
    assert quantity_tsv.startswith(
        "peptide_key\tpeptide_sequence\tmodified_peptide\tcanonical_peptide"
    )
    assert (
        "ACDM[Oxidation]K|PG002\tACDMK\tACDM[Oxidation]K\tACDMK\tPG002\tP22222\t1"
        in quantity_tsv
    )
    assert "\t890000\t\n" in quantity_tsv
    assert "\tobserved\tmissing_not_observed\n" in missingness_tsv
    assert "\t0.0048\t\n" in q_value_tsv


def test_build_diann_protein_matrix_report_applies_shared_peptide_policy() -> None:
    report = build_diann_protein_matrix_report(
        _bundle_root() / "diann_report.tsv",
        peptide_rollup_method=DiaPeptideRollupMethod.MAX,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN,
        shared_peptide_policy=DiaSharedPeptidePolicy.EXCLUDE,
        protein_rollup_method=DiaProteinRollupMethod.MAX,
    )

    assert report.target_kind is DiaProteinMatrixTargetKind.PROTEIN
    assert report.shared_peptide_policy is DiaSharedPeptidePolicy.EXCLUDE
    assert report.summary.protein_row_count == 1
    assert report.summary.excluded_shared_peptide_count == 1
    assert report.rows[0].entity_id == "P22222"


def test_render_dia_protein_matrix_exports() -> None:
    report = build_diann_protein_matrix_report(
        _bundle_root() / "diann_report.tsv",
        peptide_rollup_method=DiaPeptideRollupMethod.MAX,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN_GROUP,
        shared_peptide_policy=DiaSharedPeptidePolicy.INCLUDE,
        protein_rollup_method=DiaProteinRollupMethod.SUM,
    )

    summary_tsv = render_dia_protein_matrix_summary_tsv(report)
    quantity_tsv = render_dia_protein_quantity_matrix_tsv(report)
    missingness_tsv = render_dia_protein_missingness_tsv(report)
    q_value_tsv = render_dia_protein_q_value_matrix_tsv(report)
    evidence_tsv = render_dia_protein_rollup_evidence_tsv(report)

    assert summary_tsv.startswith(
        "source_name\ttarget_kind\tshared_peptide_policy\trollup_method"
    )
    assert "DIA-NN\tprotein_group\tinclude\tsum\t2\t2\t3\t1\t1\t0\t1\t7\t" in summary_tsv
    assert quantity_tsv.startswith(
        "entity_id\ttarget_kind\tprotein_refs\tpeptide_count\tunique_peptide_count"
    )
    assert "PG001\tprotein_group\tP11111;P11112\t1\t0\t1\tPESTIDE\t1.25e+06\t1.3e+06" in quantity_tsv
    assert (
        "PG002\tprotein_group\tP22222\t1\t1\t0\tACDM[Oxidation]K\tobserved\tmissing_not_observed"
        in missingness_tsv
    )
    assert "\t0.0021\t0.0024\n" in q_value_tsv
    assert evidence_tsv.startswith(
        "rollup_stage\ttarget_entity_level\ttarget_entity_id\tsample_id"
    )
    assert "precursor_to_peptide\tpeptide\tPESTIDE|PG001\tsample_A\tPESTIDE|z2|PG001" in evidence_tsv
    assert "peptide_to_protein\tprotein_group\tPG001\tsample_B" in evidence_tsv


def test_render_dia_protein_rollup_evidence_lists_excluded_precursors() -> None:
    report = build_diann_protein_matrix_report(
        _bundle_root() / "diann_report.tsv",
        max_q_value=0.003,
        peptide_rollup_method=DiaPeptideRollupMethod.MAX,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN_GROUP,
        shared_peptide_policy=DiaSharedPeptidePolicy.INCLUDE,
        protein_rollup_method=DiaProteinRollupMethod.SUM,
    )

    evidence_tsv = render_dia_protein_rollup_evidence_tsv(report)

    assert "q_value_threshold" in evidence_tsv
    assert "ACDM[Oxidation]K|z3|PG002" in evidence_tsv
    assert "DECOYPEP|z2|PGD01" in evidence_tsv
