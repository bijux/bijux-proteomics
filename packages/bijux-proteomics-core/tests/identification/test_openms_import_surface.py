# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.openms_import import (
    build_openms_import_report,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
    render_openms_rejected_feature_tsv,
    render_openms_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "openms"
    )


def test_openms_import_report_preserves_idxml_and_feature_table_evidence() -> None:
    root = _bundle_root()

    report = build_openms_import_report(
        root / "openms.idxml",
        feature_table_path=root / "openms_features.tsv",
    )

    assert report.summary.accepted_psm_count == 3
    assert report.summary.protein_row_count == 3
    assert report.summary.accepted_feature_count == 4
    assert report.summary.rejected_feature_count == 1
    assert report.summary.q_value_psm_count == 3
    assert report.summary.q_value_protein_count == 3
    assert report.summary.target_psm_count == 2
    assert report.summary.decoy_psm_count == 1
    assert report.summary.target_protein_count == 2
    assert report.summary.decoy_protein_count == 1
    assert report.summary.feature_sample_count == 2
    assert report.summary.feature_samples == ("sample_A", "sample_B")

    assert report.feature_parse_summary.total_rows == 5
    assert report.feature_parse_summary.accepted_rows == 4
    assert report.feature_parse_summary.rejected_rows == 1
    assert len(report.rejected_feature_rows) == 1
    assert len(report.rejected_evidence_rows) == 1

    assert report.psm_rows[0].run_id == "openms-run-01"
    assert report.psm_rows[0].spectrum_id.endswith("scan=1002")
    assert report.psm_rows[0].peptide_sequence == "SHAREDPEP"
    assert report.psm_rows[0].protein_refs == ("P11111", "P22222")
    assert report.psm_rows[0].q_value == 0.01
    assert report.psm_rows[0].provenance.source_engine == "openms-idxml"
    assert report.psm_rows[-1].target_decoy_label.value == "target"

    assert any(row.target_decoy_label.value == "decoy" for row in report.protein_rows)
    assert report.protein_rows[1].run_id == "openms-run-01"
    assert report.protein_rows[1].q_value == 0.002
    assert report.protein_rows[1].provenance.source_engine == "openms-idxml"

    feature_rows_by_id = {row.feature_id: row for row in report.feature_rows}
    assert feature_rows_by_id["feature-001"].sample_id == "sample_A"
    assert feature_rows_by_id["feature-002"].protein_refs == ("P11111", "P22222")
    assert feature_rows_by_id["feature-004"].peptide_sequence == "M[Oxidation]PEPTIDE"
    assert feature_rows_by_id["feature-004"].canonical_peptide == "M[Oxidation]PEPTIDE"
    assert (
        feature_rows_by_id["feature-001"].provenance.source_engine
        == "ms1-feature-table"
    )
    assert report.rejected_feature_rows[0].row_number == 6
    assert report.rejected_feature_rows[0].issues[0].code == "invalid_intensity"
    assert report.rejected_evidence_rows[0].source_file == "openms_features.tsv"
    assert report.rejected_evidence_rows[0].entity_type == "ms1_feature"
    assert report.rejected_evidence_rows[0].entity_id == "feature-005"
    assert report.rejected_evidence_rows[0].reason_code == "invalid_intensity"

    assert "accepted_psm_count" in render_openms_summary_tsv(report.summary)
    assert "source_engine" in render_openms_psm_tsv(report.psm_rows)
    assert "source_file" in render_openms_protein_tsv(report.protein_rows)
    assert "source_row_numbers" in render_openms_feature_tsv(report.feature_rows)
    assert "raw_fields_json" in render_openms_rejected_feature_tsv(
        report.rejected_feature_rows
    )


def test_openms_import_rejects_malformed_idxml_with_clear_location(
    tmp_path: Path,
) -> None:
    root = _bundle_root()
    malformed_idxml = tmp_path / "malformed.idxml"
    malformed_idxml.write_text(
        "\n".join(
            (
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<IdXML>",
                '  <ProteinIdentification id="openms-run-01">',
                '    <ProteinHit accession="P11111" score="0.002">',
                "  </ProteinIdentification>",
                "</IdXML>",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        build_openms_import_report(
            malformed_idxml,
            feature_table_path=root / "openms_features.tsv",
        )
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected malformed idXML to fail")

    assert "OpenMS idXML parse error" in message
    assert "line" in message
    assert "column" in message
