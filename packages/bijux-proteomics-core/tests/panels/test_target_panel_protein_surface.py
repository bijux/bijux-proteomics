# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.panels import (
    build_diann_protein_target_panel_report,
    build_lfq_protein_lfq_target_panel_report,
    build_lfq_protein_target_panel_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def _diann_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
        / name
    )


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_build_diann_protein_target_panel_report_keeps_missing_targets_visible() -> (
    None
):
    report = build_diann_protein_target_panel_report(
        _diann_fixture("diann_library_coverage.tsv"),
        _format_fixture("dia_protein_target_panel.tsv"),
    )

    assert report.source_kind.value == "dia_protein"
    assert report.summary.total_target_count == 3
    assert report.summary.matched_target_count == 2
    assert report.summary.missing_target_count == 1
    assert report.filtered_rows[0].target_id == "dia-p11111"
    assert report.filtered_rows[0].matched_entity_id == "P11111"
    assert report.filtered_rows[0].modified_peptide is None
    assert report.filtered_rows[0].expected_charge is None
    assert report.filtered_rows[1].target_id == "dia-p22222"
    assert report.missing_targets[0].target_id == "dia-missing-protein"
    assert report.missing_targets[0].modified_peptide is None
    assert report.missing_targets[0].expected_charge is None


def test_build_lfq_protein_target_panel_report_keeps_protein_intensities_visible() -> (
    None
):
    report = build_lfq_protein_target_panel_report(
        _quant_fixture("target_panel_ms1_features.tsv"),
        _format_fixture("lfq_protein_target_panel.tsv"),
    )

    assert report.source_kind.value == "lfq_protein"
    assert report.summary.total_target_count == 3
    assert report.summary.matched_target_count == 2
    assert report.summary.missing_target_count == 1
    assert report.filtered_rows[0].matched_entity_id == "P001"
    assert report.filtered_rows[1].matched_entity_id == "P003"
    assert report.missing_targets[0].target_id == "lfq-missing-protein"
    assert report.matched_targets[0].modified_peptide is None
    assert report.matched_targets[0].expected_charge is None


def test_build_lfq_protein_lfq_target_panel_report_keeps_lfq_targets_visible() -> None:
    report = build_lfq_protein_lfq_target_panel_report(
        _quant_fixture("target_panel_ms1_features.tsv"),
        _format_fixture("lfq_protein_target_panel.tsv"),
    )

    assert report.source_kind.value == "lfq_protein_lfq"
    assert report.summary.matched_target_count == 2
    assert report.filtered_rows[0].matched_entity_id == "P001"
    assert report.filtered_rows[1].matched_entity_id == "P003"
