# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.operations import (
    LabQueuePrioritizationInput,
    build_lab_queue_prioritization_report,
)


def test_build_lab_queue_prioritization_report_ranks_candidates() -> None:
    report = build_lab_queue_prioritization_report(
        (
            LabQueuePrioritizationInput(
                candidate_id="cand-a",
                candidate_score=0.9,
                evidence_gap_count=3,
                cost_score=0.3,
                capacity_pressure_score=0.2,
                assay_constraint_penalty=0.2,
            ),
            LabQueuePrioritizationInput(
                candidate_id="cand-b",
                candidate_score=0.5,
                evidence_gap_count=1,
                cost_score=0.7,
                capacity_pressure_score=0.6,
                assay_constraint_penalty=0.4,
            ),
        )
    )

    assert report.entries[0].candidate_id == "cand-a"
