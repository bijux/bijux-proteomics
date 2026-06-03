# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    LabelBasedDifferentialSourceKind,
    build_tmt_label_based_report_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_label_based_report_bundle_preserves_channel_ratio_and_differential_surfaces() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(_fixture("tmt.design.tsv")).accepted_entries
    )

    report = build_tmt_label_based_report_bundle(
        _fixture("maxquant_tmt_evidence.tsv"),
        build_experiment_design(design_entries),
        control_channel="126",
    )

    assert report.source_kind is LabelBasedDifferentialSourceKind.TMT
    assert report.tmt_matrix_report is not None
    assert report.tmt_matrix_report.summary.channel_total_count == 8
    assert report.tmt_normalization_report is not None
    assert report.tmt_ratio_report is not None
    assert report.tmt_ratio_report.summary.protein_ratio_count == 12
    assert report.tmt_validation_report is not None
    assert report.tmt_validation_report.summary.expected_channel_count == 8
    assert report.differential_analysis_report.differential_abundance_report is not None
    assert report.summary.sample_count == 8
    assert report.summary.differential_result_count == 2
