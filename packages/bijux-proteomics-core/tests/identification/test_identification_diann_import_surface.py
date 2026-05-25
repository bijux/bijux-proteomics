# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.diann_import import (
    build_diann_import_report,
    render_diann_precursor_tsv,
    render_diann_protein_group_tsv,
    render_diann_rejected_row_tsv,
    render_diann_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_diann_import_preserves_runs_samples_and_quantities() -> None:
    root = _bundle_root()

    report = build_diann_import_report(
        root / "diann_report.tsv",
        config_path=root / "diann_config.json",
    )

    assert report.summary.accepted_precursor_count == 4
    assert report.summary.rejected_precursor_count == 0
    assert report.summary.protein_group_row_count == 4
    assert report.summary.run_count == 2
    assert report.summary.sample_count == 2
    assert report.summary.precursor_quantity_count == 4
    assert report.summary.protein_group_quantity_count == 4
    assert report.summary.target_precursor_count == 3
    assert report.summary.decoy_precursor_count == 1
    assert report.summary.run_names == ("raw_A", "raw_B")
    assert report.summary.sample_names == ("sample_A", "sample_B")
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.precursor_rows[0].run_name == "raw_A"
    assert report.precursor_rows[0].sample_name == "sample_A"
    assert report.precursor_rows[0].provenance.source_engine == "diann"
    assert report.precursor_rows[0].provenance.source_row_numbers == (2,)
    assert report.precursor_rows[2].modified_peptide == "ACDM[Oxidation]K"
    assert report.precursor_rows[0].protein_group_quantity == 3400000
    assert report.precursor_rows[1].precursor_quantity == 1300000
    assert report.precursor_rows[3].target_decoy_label.value == "decoy"
    assert report.protein_group_rows[0].protein_group_id == "PG001"
    assert report.protein_group_rows[0].source_precursor_count == 1
    assert report.protein_group_rows[0].provenance.original_identifiers[
        "protein_group_id"
    ] == "PG001"
    assert report.dia_native_report.imported_precursors[0].run_name == "raw_A"
    assert report.dia_native_report.imported_precursors[0].provenance is not None
    assert {
        precursor.modified_peptide
        for precursor in report.dia_native_report.imported_precursors
    } == {"PESTIDE", "ACDM[Oxidation]K", "DECOYPEP"}
    assert report.dia_native_report.imported_count == 4
    assert len(report.dia_native_report.imported_protein_groups) == 4
    assert report.dia_native_report.imported_protein_groups[0].quantity == 3400000
    assert report.rejected_rows == ()
    assert report.rejected_evidence_rows == ()
    assert "run_names" in render_diann_summary_tsv(report.summary)
    assert "modified_peptide" in render_diann_precursor_tsv(report.precursor_rows)
    assert "protein_group_quantity" in render_diann_precursor_tsv(report.precursor_rows)
    assert "source_engine" in render_diann_precursor_tsv(report.precursor_rows)
    assert "source_precursor_count" in render_diann_protein_group_tsv(
        report.protein_group_rows
    )
    assert "original_identifiers" in render_diann_protein_group_tsv(
        report.protein_group_rows
    )
    assert "issue_codes" in render_diann_rejected_row_tsv(report.rejected_rows)


def test_diann_import_keeps_invalid_report_rows_as_explicit_rejections(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "diann_invalid.tsv"
    report_path.write_text(
        "\n".join(
            (
                "Precursor.Id\tStripped.Sequence\tModified.Sequence\tPrecursor.Charge\tQ.Value\tProtein.Group\tProtein.Ids\tRun\tSample\tPrecursor.Quantity\tPG.Quantity\tDecoy",
                "raw_A_PEPTIDE_2\tPEPTIDE\tPEPTIDE\t2\t0.01\tPG001\tP11111\traw_A\tsample_A\t50\t1000\t0",
                "raw_B_BADQ_2\tBADQ\tBADQ\t2\t1.2\tPG002\tP22222\traw_B\tsample_B\t120\t2000\t0",
                "raw_C_NEGQTY_2\tNEGQTY\tNEGQTY\t2\t0.02\tPG003\tP33333\traw_C\tsample_C\t-5\t1000\t0",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_diann_import_report(report_path)

    assert report.summary.accepted_precursor_count == 1
    assert report.summary.rejected_precursor_count == 2
    assert report.normalization is None
    issue_codes = {
        issue.code for row in report.rejected_rows for issue in row.issues
    }
    assert "invalid_q_value" in issue_codes
    assert "negative_intensity" in issue_codes
    assert len(report.rejected_evidence_rows) == 2
    assert report.rejected_evidence_rows[0].source_file == "diann_invalid.tsv"
    assert report.rejected_evidence_rows[0].entity_type == "precursor"
    assert {
        row.entity_id for row in report.rejected_evidence_rows
    } == {"raw_B_BADQ_2", "raw_C_NEGQTY_2"}
    assert {
        row.reason_code for row in report.rejected_evidence_rows
    } == {"invalid_q_value", "negative_intensity"}
    assert report.precursor_rows[0].precursor_id == "raw_A_PEPTIDE_2"
    assert report.dia_native_report.imported_protein_groups[0].quantity == 1000.0
    rejected_tsv = render_diann_rejected_row_tsv(report.rejected_rows)
    assert "raw_B_BADQ_2" in rejected_tsv
    assert "invalid_q_value" in rejected_tsv
