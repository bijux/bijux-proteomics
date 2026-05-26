# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_packets import (
    build_flagship_benchmark_recommendation_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_flagship_benchmark_recommendation_packet_family_covers_all_workflow_families() -> (
    None
):
    family = build_flagship_benchmark_recommendation_packet_family()

    assert family.family_id == "flagship-benchmark-recommendation-packets"
    assert family.artifact_path.startswith("artifacts/")
    assert len(family.packets) == 6
    assert {packet.workflow_family for packet in family.packets} == {
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }
    assert all(
        packet.artifact_path.startswith("artifacts/") for packet in family.packets
    )


def test_dia_recommendation_packet_keeps_package_context_and_caveats_visible() -> None:
    family = build_flagship_benchmark_recommendation_packet_family()

    dia = next(
        packet
        for packet in family.packets
        if packet.workflow_family is KnowledgeWorkflowFamily.DIA
    )

    assert dia.packet_id == "flagship_packet:dia"
    assert dia.benchmark_package_id == "benchmark_package:dia_library_review_package"
    assert dia.disposition.value == "recommend_with_downgrade"
    assert "vendor and library comparison gaps remain open" in dia.downgrade_chain
    assert dia.evidence_state.public_claim_support_state.value == "advisory"
    assert dia.evidence_state.ready_for_release_review is True
