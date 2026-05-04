# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.operations import (
    LabRiskDashboardInput,
    build_lab_risk_dashboard_report,
)


def test_build_lab_risk_dashboard_report_ranks_highest_composite_risk_first() -> None:
    report = build_lab_risk_dashboard_report(
        (
            LabRiskDashboardInput(
                candidate_id="c-high",
                evidence_gap_count=5,
                target_risk_score=0.9,
                sample_constraint_score=0.7,
                capacity_pressure_score=0.8,
                mitigation_actions=("add controls",),
            ),
            LabRiskDashboardInput(
                candidate_id="c-low",
                evidence_gap_count=1,
                target_risk_score=0.2,
                sample_constraint_score=0.3,
                capacity_pressure_score=0.2,
                mitigation_actions=("monitor",),
            ),
        )
    )

    assert report.entries[0].candidate_id == "c-high"
