# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_silac_label_based_report_bundle,
    build_tmt_label_based_report_bundle,
)


def _tmt_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def _silac_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_tmt_label_based_report_bundle_carries_sample_qc_rows() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_tmt_fixture("tmt.design.tsv")).accepted_entries
    )

    report = build_tmt_label_based_report_bundle(
        _tmt_fixture("maxquant_tmt_evidence.tsv"),
        design_entries,
        control_channel="126",
    )

    assert report.summary.sample_qc_entry_count == 8
    assert len(report.sample_qc_entries) == 8
    assert any(entry.flagged for entry in report.sample_qc_entries)
    assert any(
        entry.assay_axis == "129N" and entry.weak_measurement_count > 0
        for entry in report.sample_qc_entries
    )


def test_silac_label_based_report_bundle_carries_sample_qc_rows() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _silac_fixture("silac_differential.design.tsv")
        ).accepted_entries
    )

    report = build_silac_label_based_report_bundle(
        _silac_fixture("silac_differential_features.tsv"),
        design_entries,
    )

    assert report.summary.sample_qc_entry_count == 4
    assert len(report.sample_qc_entries) == 4
    assert all(entry.assay_axis == "silac" for entry in report.sample_qc_entries)
    assert all(entry.flagged is False for entry in report.sample_qc_entries)
