# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.identification.maxquant_import import (
    build_maxquant_import_report,
    render_maxquant_evidence_tsv,
    render_maxquant_lfq_candidate_tsv,
    render_maxquant_peptide_tsv,
    render_maxquant_protein_group_tsv,
    render_maxquant_summary_tsv,
)
from bijux_proteomics._scientific_tables import ScientificTableValidationError


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
    assert report.summary.lfq_candidate_count == 4
    assert report.summary.experiment_names == ("raw_A", "raw_B")
    assert report.summary.lfq_experiment_names == ("raw_A", "raw_B")
    assert report.summary.contaminant_evidence_count == 1
    assert report.summary.reverse_evidence_count == 1
    assert report.summary.contaminant_protein_group_count == 1
    assert report.summary.reverse_protein_group_count == 1
    assert report.rejected_evidence_rows == ()
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.evidence_rows[0].residue_sequence == "PESTIDE"
    assert report.evidence_rows[0].provenance.source_engine == "maxquant-evidence"
    assert report.evidence_rows[0].provenance.source_row_numbers == (2,)
    assert report.evidence_rows[0].modification_count == 1
    assert report.evidence_rows[1].protein_refs == ("P22222", "P22223")
    assert report.evidence_rows[2].contaminant_flag is True
    assert report.evidence_rows[3].reverse_flag is True
    assert report.peptide_rows[1].canonical_modified_peptide is not None
    assert report.peptide_rows[0].provenance.source_engine == "maxquant"
    assert report.protein_group_rows[0].lfq_intensities[0].experiment_name == "raw_A"
    assert report.protein_group_rows[0].provenance.original_identifiers["protein_ids"]
    assert report.protein_group_rows[0].lfq_intensities[0].provenance.source_engine == (
        "maxquant"
    )
    assert report.protein_group_rows[2].contaminant_flag is True
    assert report.protein_group_rows[3].reverse_flag is True
    assert report.lfq_matrix_candidates[2].contaminant_flag is True
    assert report.lfq_matrix_candidates[3].reverse_flag is True
    assert report.lfq_matrix_candidates[0].member_peptides == ("PESTIDE",)
    assert "experiment_names" in render_maxquant_summary_tsv(report.summary)
    assert "contaminant_flag" in render_maxquant_evidence_tsv(report.evidence_rows)
    assert "source_engine" in render_maxquant_evidence_tsv(report.evidence_rows)
    assert "leading_razor_protein" in render_maxquant_peptide_tsv(report.peptide_rows)
    assert "original_identifiers" in render_maxquant_peptide_tsv(report.peptide_rows)
    assert "lfq_intensities" in render_maxquant_protein_group_tsv(
        report.protein_group_rows
    )
    assert "source_row_numbers" in render_maxquant_protein_group_tsv(
        report.protein_group_rows
    )
    assert "member_peptides" in render_maxquant_lfq_candidate_tsv(
        report.lfq_matrix_candidates
    )


def test_maxquant_import_rejects_invalid_peptide_and_protein_group_tables(
    tmp_path: Path,
) -> None:
    evidence_path = _bundle_root() / "evidence.txt"
    peptides_path = tmp_path / "peptides.txt"
    peptides_path.write_text(
        "\n".join(
            (
                "Sequence\tModified sequence\tProteins\tLeading razor protein\tScore\tPEP\tIntensity\tMS/MS Count\tReverse\tPotential contaminant",
                "PEPTIDE\t_PEPTIDE_\tP11111\tP11111\t120\t1.2\t1000\t5\t\t0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    protein_groups_path = tmp_path / "proteinGroups.txt"
    protein_groups_path.write_text(
        "\n".join(
            (
                "Protein IDs\tMajority protein IDs\tGene names\tFasta headers\tPeptides\tRazor + unique peptides\tSequence coverage [%]\tMS/MS count\tReverse\tPotential contaminant\tOnly identified by site\tLFQ intensity raw_A",
                "P11111\tP11111\tKIN1\tsp|P11111|KINASE_HUMAN Kinase 1\t3\t2\t45.2\t5\t\t0\t0\t-10",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ScientificTableValidationError) as excinfo:
        build_maxquant_import_report(
            evidence_path,
            peptides_txt_path=peptides_path,
            protein_groups_txt_path=protein_groups_path,
        )

    issue_codes = {
        issue.code
        for row in excinfo.value.report.rejected_rows
        for issue in row.issues
    }
    assert "invalid_q_value" in issue_codes or "negative_intensity" in issue_codes


def test_maxquant_import_preserves_rejected_evidence_rows(tmp_path: Path) -> None:
    root = _bundle_root()
    evidence_path = tmp_path / "evidence_invalid.txt"
    evidence_path.write_text(
        "\n".join(
            (
                "Raw file\tExperiment\tMS/MS scan number\tSequence\tModified sequence\tCharge\tScore\tProteins\tReverse\tPotential contaminant\tPEP",
                "raw_A\traw_A\t1001\tPESTIDE\tPES(Phospho (STY))TIDE\t2\t120\tP11111\t\t\t0.001",
                "raw_B\traw_B\t1002\tBROKEN\tBROKEN\tbad\t95\tP22222\t\t\t0.01",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_maxquant_import_report(
        evidence_path,
        peptides_txt_path=root / "peptides.txt",
        protein_groups_txt_path=root / "proteinGroups.txt",
    )

    assert report.summary.accepted_evidence_count == 1
    assert report.summary.rejected_evidence_count == 1
    assert len(report.rejected_evidence_rows) == 1
    assert report.rejected_evidence_rows[0].source_file == "evidence_invalid.txt"
    assert report.rejected_evidence_rows[0].entity_type == "psm"
    assert report.rejected_evidence_rows[0].entity_id == "1002"
    assert report.rejected_evidence_rows[0].reason_code == "invalid_charge"
