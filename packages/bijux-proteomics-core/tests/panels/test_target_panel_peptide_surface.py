# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.panels import (
    build_diann_peptide_target_panel_report,
    build_lfq_peptide_target_panel_report,
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


def test_build_diann_peptide_target_panel_report_keeps_matched_and_missing_targets_visible() -> (
    None
):
    report = build_diann_peptide_target_panel_report(
        _diann_fixture("diann_library_coverage.tsv"),
        _format_fixture("dia_target_panel.tsv"),
    )

    assert report.source_kind.value == "dia_peptide"
    assert report.summary.total_target_count == 4
    assert report.summary.matched_target_count == 3
    assert report.summary.missing_target_count == 1
    assert report.summary.matched_entity_count == 3
    assert report.summary.sample_count == 3
    assert report.matched_targets[0].modified_peptide == "PEPALFA"
    assert report.matched_targets[0].expected_charge == 2
    assert report.matched_targets[1].target_id == "dia-p22222"
    assert report.matched_targets[1].detected_sample_count == 2
    assert report.filtered_rows[1].target_id == "dia-p22222"
    assert report.filtered_rows[1].peptide_sequence == "PEPGAMMA"
    assert report.filtered_rows[0].modified_peptide == "PEPALFA"
    assert report.filtered_rows[0].expected_charge == 2
    assert report.filtered_rows[0].charge_states == (2,)
    assert report.missing_targets[0].target_id == "dia-missing-protein"
    assert report.missing_targets[0].modified_peptide is None
    assert report.missing_targets[0].expected_charge is None
    assert report.intensity_entries[0].target_id == "dia-pepalfa"
    assert report.intensity_entries[0].modified_peptide == "PEPALFA"
    assert report.intensity_entries[0].expected_charge == 2


def test_build_lfq_peptide_target_panel_report_keeps_target_intensities_visible() -> (
    None
):
    report = build_lfq_peptide_target_panel_report(
        _quant_fixture("target_panel_ms1_features.tsv"),
        _format_fixture("lfq_target_panel.tsv"),
    )

    assert report.source_kind.value == "lfq_peptide"
    assert report.summary.total_target_count == 4
    assert report.summary.matched_target_count == 3
    assert report.summary.missing_target_count == 1
    assert report.summary.sample_count == 4
    assert report.filtered_rows[0].target_id == "lfq-apeptide"
    assert report.filtered_rows[0].peptide_sequence == "APEPTIDE"
    assert report.filtered_rows[0].modified_peptide == "APEPTIDE"
    assert report.filtered_rows[0].expected_charge == 2
    assert report.filtered_rows[0].charge_states == (2,)
    assert report.filtered_rows[1].target_id == "lfq-cpeptide"
    assert report.filtered_rows[1].peptide_sequence == "CPEPTIDE"
    assert report.filtered_rows[2].target_id == "lfq-p003"
    assert report.filtered_rows[2].protein_refs == ("P003",)
    assert report.missing_targets[0].target_id == "lfq-missing-peptide"
    assert report.missing_targets[0].modified_peptide == "ZPEPTIDE"
    assert report.missing_targets[0].expected_charge == 2
