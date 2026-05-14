# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.spectronaut_import import (
    build_spectronaut_import_report,
    render_spectronaut_precursor_tsv,
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
    assert report.summary.modified_precursor_count == 3
    assert report.summary.sample_count == 2
    assert report.summary.run_count == 2
    assert report.summary.precursor_quantity_count == 4
    assert report.summary.protein_group_quantity_count == 4
    assert report.summary.target_precursor_count == 3
    assert report.summary.decoy_precursor_count == 1
    assert report.summary.sample_names == ("sample_A", "sample_B")
    assert report.summary.run_names == ("raw_A", "raw_B")
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.precursor_rows[0].sample_name == "sample_A"
    assert report.precursor_rows[0].modified_peptide == "PES[Phospho]TIDE"
    assert report.precursor_rows[0].canonical_modified_peptide == "PES[Phospho]TIDE"
    assert report.precursor_rows[1].protein_group_quantity == 3950000
    assert report.precursor_rows[3].target_decoy_label.value == "decoy"
    assert report.protein_group_rows[0].protein_group_id == "PG001"
    assert report.protein_group_rows[0].source_precursor_count == 1
    assert "modified_precursor_count" in render_spectronaut_summary_tsv(report.summary)
    assert "canonical_modified_peptide" in render_spectronaut_precursor_tsv(
        report.precursor_rows
    )
    assert "source_precursor_count" in render_spectronaut_protein_group_tsv(
        report.protein_group_rows
    )
