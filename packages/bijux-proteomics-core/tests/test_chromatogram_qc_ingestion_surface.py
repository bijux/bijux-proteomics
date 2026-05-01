# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.advanced_format_ingestion import parse_chromatogram_qc_table


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def test_parse_chromatogram_qc_table_distinguishes_unknown_from_failed_metrics() -> (
    None
):
    report = parse_chromatogram_qc_table(_format_fixture("chromatogram_qc.tsv"))

    assert report.total_rows == 4
    assert len(report.accepted_points) == 3
    assert report.unknown_metric_rows == 1
    assert report.failed_metric_rows == 1
