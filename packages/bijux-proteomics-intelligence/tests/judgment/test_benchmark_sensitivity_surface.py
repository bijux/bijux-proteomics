# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_sensitivity import (
    build_flagship_benchmark_sensitivity_report,
)


def test_flagship_benchmark_sensitivity_report_shows_policy_changes() -> None:
    report = build_flagship_benchmark_sensitivity_report()

    assert report.report_id == "flagship-benchmark-ranking-sensitivity"
    assert report.artifact_path.startswith("artifacts/")
    assert report.changed_scenario_ids
    assert any(
        scenario.scenario_id == "refuse-thin-targeted-and-ptm-promotion"
        and scenario.changed
        for scenario in report.scenarios
    )
