# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.operations import (
    AssayExpectedEvidenceGainInput,
    build_assay_expected_evidence_gain_report,
)


def test_build_assay_expected_evidence_gain_report_estimates_value_and_bounds() -> None:
    report = build_assay_expected_evidence_gain_report(
        (
            AssayExpectedEvidenceGainInput(
                action_id="act-1",
                contradiction_resolution_potential=0.8,
                validation_coverage_gain=0.6,
                execution_feasibility=0.7,
                uncertainty_fraction=0.25,
            ),
        )
    )

    entry = report.entries[0]
    assert entry.expected_decision_value > 0.6
    assert entry.low_value < entry.expected_decision_value < entry.high_value
