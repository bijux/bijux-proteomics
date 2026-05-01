# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration16 import (
    PlateRandomizationRequest,
    PlateRandomizationStrategy,
    build_plate_randomization_plan,
)


def test_build_plate_randomization_plan_is_seed_reproducible() -> None:
    request = PlateRandomizationRequest(
        plate_id="plate-a",
        strategy=PlateRandomizationStrategy.FULL_RANDOM,
        sample_ids=("s1", "s2", "s3", "s4"),
        seed=42,
    )
    first = build_plate_randomization_plan(request)
    second = build_plate_randomization_plan(request)

    assert first.supported is True
    assert first.assignment_order == second.assignment_order
