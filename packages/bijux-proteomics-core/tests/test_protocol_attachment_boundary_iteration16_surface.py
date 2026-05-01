# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab_planning_iteration16 import (
    ProtocolAttachmentInput,
    evaluate_protocol_attachment_boundary,
)


def test_evaluate_protocol_attachment_boundary_refuses_protocol_truth_claims() -> None:
    report = evaluate_protocol_attachment_boundary(
        ProtocolAttachmentInput(
            protocol_id="sop-42",
            protocol_version="2.1",
            claims_protocol_truth=True,
            has_protocol_registry_reference=True,
        )
    )

    assert report.attached is False
    assert "refused" in report.reason
