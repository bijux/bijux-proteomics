# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration10 import (
    AssayDesignProfile,
    compare_assay_designs,
)


def test_compare_assay_designs_prefers_higher_evidence_gain_under_capacity() -> None:
    report = compare_assay_designs(
        (
            AssayDesignProfile(
                design_id="design-a",
                multiplex_channels=10,
                fraction_count=6,
                control_count=2,
                replicate_count=3,
                capacity_demand=2.0,
                expected_evidence_gain=0.75,
            ),
            AssayDesignProfile(
                design_id="design-b",
                multiplex_channels=6,
                fraction_count=4,
                control_count=1,
                replicate_count=2,
                capacity_demand=1.2,
                expected_evidence_gain=0.55,
            ),
        )
    )

    assert report.preferred_design_id == "design-a"
    assert report.entries[0].score > report.entries[1].score
