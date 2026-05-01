# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review_iteration09 import (
    ContradictionObservation,
    classify_contradictions,
)


def test_classify_contradictions_assigns_deterministic_categories() -> None:
    report = classify_contradictions(
        (
            ContradictionObservation(
                contradiction_id="cx-1",
                left_evidence_id="E1",
                right_evidence_id="E2",
                left_source="study-a",
                right_source="study-b",
                left_method="dia",
                right_method="dia",
                left_score=0.92,
                right_score=0.90,
                left_quant_state="up",
                right_quant_state="up",
                left_ptm_state="present",
                right_ptm_state="present",
                left_qc_state="pass",
                right_qc_state="pass",
                left_lab_outcome="confirmed",
                right_lab_outcome="confirmed",
            ),
            ContradictionObservation(
                contradiction_id="cx-2",
                left_evidence_id="E3",
                right_evidence_id="E4",
                left_source="study-c",
                right_source="study-c",
                left_method="dia",
                right_method="dda",
                left_score=0.81,
                right_score=0.80,
                left_quant_state="up",
                right_quant_state="up",
                left_ptm_state="present",
                right_ptm_state="present",
                left_qc_state="pass",
                right_qc_state="pass",
                left_lab_outcome="confirmed",
                right_lab_outcome="confirmed",
            ),
        )
    )

    categories = {entry.contradiction_id: entry.category for entry in report.entries}
    assert categories["cx-1"] == "source_disagreement"
    assert categories["cx-2"] == "method_disagreement"
    assert report.category_counts["source_disagreement"] == 1
    assert report.category_counts["method_disagreement"] == 1
