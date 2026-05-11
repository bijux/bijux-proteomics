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
