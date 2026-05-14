# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.benchmarks import (
    ReviewPacketScaleBenchmarkInput,
    build_review_packet_scale_benchmark_report,
)


def test_build_review_packet_scale_benchmark_report_reports_navigation_bottleneck() -> (
    None
):
    fixture = json.loads(
        (
            Path(__file__).resolve().parent.parent
            / "fixtures"
            / "benchmarks"
            / "review_packet_scale_medium.json"
        ).read_text(encoding="utf-8")
    )
    report = build_review_packet_scale_benchmark_report(
        ReviewPacketScaleBenchmarkInput(
            candidate_count=int(fixture["candidate_count"]),
            evidence_entry_count=int(fixture["evidence_entry_count"]),
            render_seconds=float(fixture["render_seconds"]),
            navigation_seconds=float(fixture["navigation_seconds"]),
            export_seconds=float(fixture["export_seconds"]),
        )
    )

    assert report.bottleneck_stage == "navigation"
    assert report.candidate_count == 5200
