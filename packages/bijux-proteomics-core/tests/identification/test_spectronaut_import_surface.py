# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.identification.spectronaut_import import (
    build_spectronaut_import_report,
    render_spectronaut_precursor_quantity_tsv,
    render_spectronaut_precursor_tsv,
    render_spectronaut_protein_group_quantity_tsv,
    render_spectronaut_protein_group_tsv,
    render_spectronaut_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "spectronaut"
    )


def test_spectronaut_import_preserves_samples_quantities_and_modified_peptides() -> (
    None
):
    root = _bundle_root()

    report = build_spectronaut_import_report(
        root / "spectronaut_report.tsv",
        config_path=root / "spectronaut_settings.txt",
    )

    assert report.summary.accepted_precursor_count == 4
    assert report.summary.rejected_precursor_count == 0
    assert report.summary.protein_group_row_count == 4
    assert report.summary.precursor_quantity_row_count == 4
    assert report.summary.protein_group_quantity_row_count == 4
    assert report.summary.modified_precursor_count == 3
    assert report.summary.sample_count == 2
    assert report.summary.run_count == 2
    assert report.summary.precursor_quantity_count == 4
    assert report.summary.protein_group_quantity_count == 4
    assert report.summary.target_precursor_count == 3
    assert report.summary.decoy_precursor_count == 1
    assert report.rejected_evidence_rows == ()
    assert report.summary.sample_names == ("sample_A", "sample_B")
    assert report.summary.run_names == ("raw_A", "raw_B")
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.precursor_evidence_rows == report.precursor_rows
    assert report.precursor_rows[0].sample_name == "sample_A"
    assert report.precursor_rows[0].provenance.source_engine == "spectronaut"
    assert report.precursor_rows[0].provenance.source_row_numbers == (2,)
    assert report.precursor_rows[0].modified_peptide == "PES[Phospho]TIDE"
    assert report.precursor_rows[0].canonical_modified_peptide == "PES[Phospho]TIDE"
    assert report.precursor_rows[1].protein_group_quantity == 3950000
    assert report.precursor_rows[3].target_decoy_label.value == "decoy"
    assert report.protein_group_rows[0].protein_group_id == "PG001"
    assert report.protein_group_rows[0].source_precursor_count == 1
    assert (
        report.protein_group_rows[0].provenance.original_identifiers["protein_group_id"]
        == "PG001"
    )
    assert report.precursor_quantity_rows[0].precursor_id == "sn_rawA_pestide_2"
    assert report.precursor_quantity_rows[0].precursor_quantity == 1420000
    assert report.precursor_quantity_rows[0].provenance.source_engine == "spectronaut"
    assert report.protein_group_quantity_rows[0].protein_group_id == "PG001"
    assert report.protein_group_quantity_rows[0].protein_group_quantity == 3800000
    assert "modified_precursor_count" in render_spectronaut_summary_tsv(report.summary)
    assert "canonical_modified_peptide" in render_spectronaut_precursor_tsv(
        report.precursor_rows
    )
    assert "source_engine" in render_spectronaut_precursor_tsv(report.precursor_rows)
    assert "source_precursor_count" in render_spectronaut_protein_group_tsv(
        report.protein_group_rows
    )
    assert "precursor_quantity" in render_spectronaut_precursor_quantity_tsv(
        report.precursor_quantity_rows
    )
    assert "original_identifiers" in render_spectronaut_precursor_quantity_tsv(
        report.precursor_quantity_rows
    )
    assert "protein_group_quantity" in render_spectronaut_protein_group_quantity_tsv(
        report.protein_group_quantity_rows
    )


def test_spectronaut_import_rejects_missing_required_export_columns(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "spectronaut_missing_columns.tsv"
    report_path.write_text(
        "\n".join(
            (
                "EG.PrecursorId\tPEP.StrippedSequence\tFG.Charge\tEG.Cscore\tEG.Qvalue\tPG.ProteinGroups\tPG.ProteinAccessions\tR.FileName\tR.Condition\tFG.Quantity\tPG.Quantity\tEG.IsDecoy",
                "raw_A_PEPTIDE_2\tPEPTIDE\t2\t0.98\t0.01\tPG001\tP11111\traw_A\tsample_A\t1500000\t3500000\tFalse",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Spectronaut schema error"):
        build_spectronaut_import_report(report_path)


def test_spectronaut_import_preserves_rejected_evidence_rows(tmp_path: Path) -> None:
    report_path = tmp_path / "spectronaut_invalid.tsv"
    report_path.write_text(
        "\n".join(
            (
                "EG.PrecursorId\tPEP.StrippedSequence\tFG.LabeledSequence\tFG.Charge\tEG.Cscore\tEG.Qvalue\tPG.ProteinGroups\tPG.ProteinAccessions\tR.FileName\tR.Condition\tFG.Quantity\tPG.Quantity\tEG.IsDecoy",
                "sn_rawA_pestide_2\tPESTIDE\tPES[Phospho]TIDE\t2\t0.98\t0.01\tPG001\tP11111\traw_A\tsample_A\t1500000\t3500000\tFalse",
                "sn_rawB_broken_2\tBROKEN\tBROKEN\tbad\t0.75\t0.02\tPG002\tP22222\traw_B\tsample_B\t1200000\t2500000\tFalse",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_spectronaut_import_report(report_path)

    assert report.summary.accepted_precursor_count == 1
    assert report.summary.rejected_precursor_count == 1
    assert len(report.rejected_evidence_rows) == 1
    assert report.rejected_evidence_rows[0].source_file == "spectronaut_invalid.tsv"
    assert report.rejected_evidence_rows[0].entity_type == "precursor"
    assert report.rejected_evidence_rows[0].entity_id == "sn_rawB_broken_2"
    assert report.rejected_evidence_rows[0].reason_code == "invalid_charge"
