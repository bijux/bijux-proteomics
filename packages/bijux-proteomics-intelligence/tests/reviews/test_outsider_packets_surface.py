# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.outsider_packets import (
    build_flagship_outsider_review_packet,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_flagship_outsider_review_packet_family_covers_five_flagship_workflows() -> None:
    family = build_flagship_outsider_review_packet_family()

    assert family.family_id == "flagship-outsider-review-packets"
    assert tuple(packet.workflow_family for packet in family.packets) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )


def test_dda_outsider_packet_is_complete_and_links_to_shipped_public_evidence() -> None:
    packet = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.DDA)

    assert packet.complete_outsider_surface is True
    assert packet.runtime_package_id == "dda-maxquant-pipeline-corpus"
    assert packet.runtime_run_mode.value == "import_only"
    assert packet.benchmark_package_id == "benchmark_package:dda_reviewable_run"
    assert any(
        link.repo_relative_path.endswith(
            "public_benchmark_packages/dda_reviewable_run/package_manifest.json"
        )
        for link in packet.primary_data_links
    )
    assert any(
        link.repo_relative_path.endswith(
            "search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv"
        )
        for link in packet.review_artifact_links
    )
    assert any(
        "cross-engine" in context or "MSFragger" in context
        for context in packet.comparator_context
    )
    assert "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py" in packet.validating_tests


def test_non_dda_outsider_packets_keep_missing_public_proof_explicit() -> None:
    dia = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.DIA)
    lfq = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.LFQ)
    ptm = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.PTM)
    targeted = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.TARGETED)

    assert dia.complete_outsider_surface is False
    assert any("curated_mini_study" in reason for reason in dia.missing_surface_reasons)
    assert lfq.runtime_run_mode.value == "blocked"
    assert any("no flagship runtime benchmark path is wired" in reason for reason in lfq.missing_surface_reasons)
    assert ptm.public_claim_support_state.value == "refused"
    assert any("public comparator-backed claim support is still refused" in reason for reason in ptm.missing_surface_reasons)
    assert targeted.runtime_package_id is None
    assert any("no flagship runtime truth row is published" in reason for reason in targeted.missing_surface_reasons)
