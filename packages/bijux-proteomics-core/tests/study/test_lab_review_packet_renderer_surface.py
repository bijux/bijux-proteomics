# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study.laboratory_plans import (
    LabReviewPacketInput,
    build_lab_review_packet_rendering,
    render_lab_review_packet,
)


def test_render_lab_review_packet_bundles_required_lab_review_sections() -> None:
    payload = LabReviewPacketInput(
        packet_id="lab-packet-1",
        assay_rationale="validate top-ranked phospho candidates",
        target_evidence_ids=("E1", "E2"),
        control_ids=("QC-POOL",),
        risk_ids=("risk-material",),
        capacity_summary="12 instrument-hours available, 10 required",
        handoff_files=("handoff.tsv", "handoff.json"),
    )
    packet = build_lab_review_packet_rendering(payload)
    assert render_lab_review_packet(payload) == packet

    assert packet.packet_id == "lab-packet-1"
    assert '"packet_id":"lab-packet-1"' in packet.packet_json
    assert "Target evidence: E1, E2" in packet.packet_markdown
