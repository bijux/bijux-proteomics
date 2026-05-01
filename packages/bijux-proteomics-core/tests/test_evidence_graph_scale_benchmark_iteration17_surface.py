# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.scale_iteration17 import (
    EvidenceGraphScaleBenchmarkInput,
    build_evidence_graph_scale_benchmark_report,
)


def test_build_evidence_graph_scale_benchmark_report_finds_bottleneck() -> None:
    report = build_evidence_graph_scale_benchmark_report(
        EvidenceGraphScaleBenchmarkInput(
            node_count=150_000,
            edge_count=320_000,
            build_seconds=40.0,
            query_seconds=18.0,
            packet_seconds=24.0,
            export_seconds=12.0,
        )
    )

    assert report.total_seconds == 94.0
    assert report.bottleneck_stage == "build"
