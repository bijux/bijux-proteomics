# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.maxquant_import import (
    build_maxquant_import_report,
    render_maxquant_evidence_tsv,
    render_maxquant_peptide_tsv,
    render_maxquant_protein_group_tsv,
    render_maxquant_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "maxquant"
    )


def test_maxquant_import_preserves_experiments_lfq_and_flags() -> None:
    root = _bundle_root()

    report = build_maxquant_import_report(
        root / "evidence.txt",
        peptides_txt_path=root / "peptides.txt",
        protein_groups_txt_path=root / "proteinGroups.txt",
        config_path=root / "maxquant_settings.txt",
    )

    assert report.summary.accepted_evidence_count == 4
    assert report.summary.rejected_evidence_count == 0
    assert report.summary.peptide_row_count == 4
    assert report.summary.protein_group_row_count == 4
    assert report.summary.modified_evidence_count == 2
    assert report.summary.modified_peptide_row_count == 2
    assert report.summary.experiment_count == 2
    assert report.summary.lfq_experiment_count == 2
    assert report.summary.experiment_names == ("raw_A", "raw_B")
    assert report.summary.lfq_experiment_names == ("raw_A", "raw_B")
    assert report.summary.contaminant_evidence_count == 1
    assert report.summary.reverse_evidence_count == 1
    assert report.summary.contaminant_protein_group_count == 1
    assert report.summary.reverse_protein_group_count == 1
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.evidence_rows[0].residue_sequence == "PESTIDE"
    assert report.evidence_rows[0].modification_count == 1
    assert report.evidence_rows[1].protein_refs == ("P22222", "P22223")
    assert report.evidence_rows[2].contaminant_flag is True
    assert report.evidence_rows[3].reverse_flag is True
    assert report.peptide_rows[1].canonical_modified_peptide is not None
    assert report.protein_group_rows[0].lfq_intensities[0].experiment_name == "raw_A"
    assert report.protein_group_rows[2].contaminant_flag is True
    assert report.protein_group_rows[3].reverse_flag is True
    assert "experiment_names" in render_maxquant_summary_tsv(report.summary)
    assert "contaminant_flag" in render_maxquant_evidence_tsv(report.evidence_rows)
    assert "leading_razor_protein" in render_maxquant_peptide_tsv(report.peptide_rows)
    assert "lfq_intensities" in render_maxquant_protein_group_tsv(
        report.protein_group_rows
    )
