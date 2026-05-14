# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.openms_import import (
    build_openms_import_report,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
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

    assert report.psm_rows[0].run_id == "openms-run-01"
    assert report.psm_rows[0].spectrum_id.endswith("scan=1002")
    assert report.psm_rows[0].peptide_sequence == "SHAREDPEP"
    assert report.psm_rows[0].protein_refs == ("P11111", "P22222")
    assert report.psm_rows[0].q_value == 0.01
    assert report.psm_rows[-1].target_decoy_label.value == "target"

    assert any(row.target_decoy_label.value == "decoy" for row in report.protein_rows)
    assert report.protein_rows[1].run_id == "openms-run-01"
    assert report.protein_rows[1].q_value == 0.002

    feature_rows_by_id = {row.feature_id: row for row in report.feature_rows}
    assert feature_rows_by_id["feature-001"].sample_id == "sample_A"
    assert feature_rows_by_id["feature-002"].protein_refs == ("P11111", "P22222")
    assert feature_rows_by_id["feature-004"].peptide_sequence == "M[Oxidation]PEPTIDE"
    assert feature_rows_by_id["feature-004"].canonical_peptide == "M[Oxidation]PEPTIDE"

    assert "accepted_psm_count" in render_openms_summary_tsv(report.summary)
    assert "protein_refs" in render_openms_psm_tsv(report.psm_rows)
    assert "target_decoy_label" in render_openms_protein_tsv(report.protein_rows)
    assert "canonical_peptide" in render_openms_feature_tsv(report.feature_rows)
