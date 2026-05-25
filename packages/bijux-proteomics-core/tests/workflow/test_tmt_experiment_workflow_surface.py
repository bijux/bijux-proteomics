# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.workflow import build_tmt_experiment_workflow_bundle


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_build_tmt_experiment_workflow_bundle_preserves_import_metadata_and_report() -> (
    None
):
    report = build_tmt_experiment_workflow_bundle(
        _multiplex_fixture("maxquant_tmt_interference.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    assert report.source_kind is TmtSearchResultSourceKind.MAXQUANT
    assert report.summary.accepted_input_row_count == 4
    assert report.summary.rejected_input_row_count == 0
    assert report.summary.design_row_count == 8
    assert report.summary.multiplex_group_count == 2
    assert report.summary.mapped_channel_count == 8
    assert report.summary.missing_source_channel_count == 2
    assert report.summary.protein_row_count == 2
    assert report.summary.protein_ratio_count == 12
    assert report.summary.differential_result_count == 2
    assert report.summary.sample_qc_entry_count == 8
    assert report.summary.interference_observation_count == 12
    assert report.summary.flagged_interference_count == 6
    assert report.metadata_validation_report.summary.duplicate_assignment_count == 0
    assert report.metadata_validation_report.summary.missing_condition_count == 0
    assert report.interference_report.summary.threshold_exceeded_count == 6
    assert report.report.tmt_matrix_report is not None
    assert report.report.tmt_matrix_report.source_report.summary.reporter_channel_count == 3
    assert report.report.differential_analysis_report.differential_abundance_report is not None


def test_build_tmt_experiment_workflow_bundle_preserves_rejected_reporter_review() -> (
    None
):
    report = build_tmt_experiment_workflow_bundle(
        _workflow_fixture("tmt_reporter_parse_issues.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    assert report.summary.accepted_input_row_count == 4
    assert report.summary.rejected_input_row_count == 1
    assert report.report.tmt_matrix_report is not None
    assert report.report.tmt_matrix_report.source_report.rejected_rows[0].row_number == 6
    assert {
        issue.code
        for issue in report.report.tmt_matrix_report.source_report.rejected_rows[0].issues
    } == {"missing_peptide", "invalid_reporter_intensity"}


def test_build_tmt_experiment_workflow_bundle_rejects_invalid_metadata() -> None:
    with pytest.raises(
        ValueError,
        match="unique multiplex channel and sample assignments",
    ):
        build_tmt_experiment_workflow_bundle(
            _multiplex_fixture("maxquant_tmt_evidence.tsv"),
            _multiplex_fixture("tmt_duplicate_channel.design.tsv"),
            control_channel="126",
            source_kind=TmtSearchResultSourceKind.MAXQUANT,
        )


def test_build_tmt_experiment_workflow_bundle_rejects_missing_channel_coverage() -> None:
    with pytest.raises(
        ValueError,
        match="complete multiplex channel coverage",
    ):
        build_tmt_experiment_workflow_bundle(
            _multiplex_fixture("maxquant_tmt_evidence.tsv"),
            _multiplex_fixture("tmt_missing_channel.design.tsv"),
            control_channel="126",
            source_kind=TmtSearchResultSourceKind.MAXQUANT,
        )
