# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.laboratory_operations import (
    LabCostModelInput,
    build_lab_cost_model_report,
)


def test_build_lab_cost_model_report_includes_uncertainty_bounds() -> None:
    report = build_lab_cost_model_report(
        (
            LabCostModelInput(
                action_id="assay-1",
                reagent_cost=120.0,
                instrument_cost=280.0,
                staff_cost=80.0,
                opportunity_cost=20.0,
                uncertainty_fraction=0.2,
            ),
        )
    )

    entry = report.entries[0]
    assert entry.expected_total_cost == 500.0
    assert entry.low_estimate == 400.0
    assert entry.high_estimate == 600.0
