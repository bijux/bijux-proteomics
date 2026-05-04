# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study import (
    LabRequestSchema,
    LabRequestTarget,
    validate_lab_request_schema,
)


def test_validate_lab_request_schema_rejects_missing_targets_controls_and_evidence() -> (
    None
):
    report = validate_lab_request_schema(
        LabRequestSchema(
            request_id="req-001",
            method="unsupported_method",
            target_entries=(
                LabRequestTarget(
                    target_id="t1", assay_type="PTM", expected_evidence=()
                ),
            ),
            sample_ids=(),
            control_ids=(),
            constraints=("max_injection_time=100ms",),
        )
    )

    codes = {issue.code for issue in report.issues}
    assert report.valid is False
    assert "missing_samples" in codes
    assert "missing_controls" in codes
    assert "unsupported_method" in codes
    assert "target_missing_expected_evidence" in codes
