# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study import (
    PlateLayoutEntry,
    validate_plate_layout,
)


def test_validate_plate_layout_rejects_invalid_positions_and_missing_controls() -> None:
    report = validate_plate_layout(
        (
            PlateLayoutEntry(
                sample_id="sample-01",
                replicate_id="R1",
                well_position="Z9",
                control=False,
                randomized=False,
            ),
            PlateLayoutEntry(
                sample_id="sample-01",
                replicate_id="R2",
                well_position="A1",
                control=False,
                randomized=False,
            ),
            PlateLayoutEntry(
                sample_id="sample-02",
                replicate_id="R1",
                well_position="A1",
                control=False,
                randomized=False,
            ),
        ),
        capacity=2,
    )

    codes = {issue.code for issue in report.issues}
    assert report.valid is False
    assert "capacity_exceeded" in codes
    assert "invalid_well_position" in codes
    assert "duplicate_well_position" in codes
    assert "missing_controls" in codes
    assert "missing_randomization" in codes
    assert "missing_replicate_layout" in codes
