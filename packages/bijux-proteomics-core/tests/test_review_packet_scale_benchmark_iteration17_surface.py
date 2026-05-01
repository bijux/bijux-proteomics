# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    ReviewPacketScaleBenchmarkInput,
    build_review_packet_scale_benchmark_report,
)


def test_build_review_packet_scale_benchmark_report_reports_navigation_bottleneck() -> (
    None
):
    report = build_review_packet_scale_benchmark_report(
        ReviewPacketScaleBenchmarkInput(
            candidate_count=5000,
            evidence_entry_count=180_000,
            render_seconds=28.0,
            navigation_seconds=36.0,
            export_seconds=12.0,
        )
    )

    assert report.bottleneck_stage == "navigation"
