# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment import (
    build_flagship_benchmark_decision_policy,
    build_flagship_benchmark_recommendation_packet_family,
    build_flagship_benchmark_sensitivity_report,
)


def test_judgment_namespace_exposes_benchmark_decision_surfaces() -> None:
    assert build_flagship_benchmark_decision_policy().policy_id == (
        "flagship-benchmark-decision"
    )
    assert build_flagship_benchmark_recommendation_packet_family().family_id == (
        "flagship-benchmark-recommendation-packets"
    )
    assert build_flagship_benchmark_sensitivity_report().report_id == (
        "flagship-benchmark-ranking-sensitivity"
    )
