# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration10 import build_capacity_model_with_uncertainty


def test_build_capacity_model_with_uncertainty_marks_constrained_when_overbooked() -> None:
    model = build_capacity_model_with_uncertainty(
        instrument_hours_available=12.0,
        instrument_hours_required=14.0,
        sample_count=24,
        fraction_count=48,
        queue_depth=3,
        budget_available=2000.0,
        budget_required=1800.0,
        schedule_uncertainty=0.1,
        budget_uncertainty=0.05,
    )

    assert model.time_utilization_ratio > 1.0
    assert model.constrained is True
