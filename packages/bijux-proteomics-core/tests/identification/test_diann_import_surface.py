# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.diann_import import (
    build_diann_import_report,
    render_diann_precursor_tsv,
    render_diann_protein_group_tsv,
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
    assert report.precursor_rows[0].protein_group_quantity == 3400000
    assert report.precursor_rows[1].precursor_quantity == 1300000
    assert report.precursor_rows[3].target_decoy_label.value == "decoy"
    assert report.protein_group_rows[0].protein_group_id == "PG001"
    assert report.protein_group_rows[0].source_precursor_count == 1
    assert report.dia_native_report.imported_count == 4
    assert len(report.dia_native_report.imported_protein_groups) == 3
    assert "run_names" in render_diann_summary_tsv(report.summary)
    assert "protein_group_quantity" in render_diann_precursor_tsv(report.precursor_rows)
    assert "source_precursor_count" in render_diann_protein_group_tsv(
        report.protein_group_rows
    )
