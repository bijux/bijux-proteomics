# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from types import SimpleNamespace

import pytest

from bijux_proteomics_intelligence.reviews.outsider_packets import (
    build_flagship_outsider_review_packet,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_flagship_outsider_review_packet_family_covers_five_flagship_workflows() -> (
    None
):
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
    assert packet.runtime_run_mode is not None

    assert packet.complete_outsider_surface is True
    assert packet.runtime_package_id == "dda-maxquant-pipeline-corpus"
    assert packet.runtime_run_mode.value == "import_only"
    assert packet.benchmark_package_id == "benchmark_package:dda_reviewable_run"
    assert any(
        link.repo_relative_path.endswith(
            "benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json"
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
    assert packet.lab_outcome_dossier_id == "flagship_follow_up_outcome:dda"
    assert packet.assay_worth_it is True
    assert (
        "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py"
        in packet.validating_tests
    )


def test_dia_outsider_packet_is_complete_but_keeps_library_limits_visible() -> None:
    dia = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.DIA)
    assert dia.runtime_run_mode is not None

    assert dia.complete_outsider_surface is True
    assert dia.runtime_package_id == "dia-diann-pipeline-corpus"
    assert dia.runtime_run_mode.value == "raw_executable"
    assert dia.public_claim_support_state.value == "advisory"
    assert dia.outcome_recommendation_disposition.value == "do_not_recommend"
    assert dia.assay_worth_it is False
    assert any(
        "outside the repository proof boundary" in reason
        for reason in dia.missing_surface_reasons
    )


def test_lfq_ptm_and_targeted_outsider_packets_are_bounded_but_complete() -> None:
    lfq = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.LFQ)
    ptm = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.PTM)
    targeted = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.TARGETED)
    assert lfq.runtime_run_mode is not None
    assert ptm.runtime_run_mode is not None
    assert targeted.runtime_run_mode is not None

    assert lfq.complete_outsider_surface is False
    assert lfq.runtime_run_mode.value == "raw_executable"
    assert lfq.public_claim_support_state.value == "advisory"
    assert lfq.recommendation_disposition.value == "recommend_with_downgrade"
    assert any(
        "external execution parity" in reason for reason in lfq.missing_surface_reasons
    )
    assert any(
        "release language is ahead of the benchmark evidence" in reason
        for reason in lfq.missing_surface_reasons
    )
    assert ptm.complete_outsider_surface is True
    assert ptm.public_claim_support_state.value == "advisory"
    assert ptm.runtime_run_mode.value == "raw_executable"
    assert any(
        "external execution parity" in reason for reason in ptm.missing_surface_reasons
    )
    assert targeted.runtime_package_id == "targeted-transition-review-corpus"
    assert targeted.complete_outsider_surface is True
    assert targeted.runtime_run_mode.value == "raw_executable"
    assert targeted.public_claim_support_state.value == "advisory"
    assert targeted.lab_outcome_dossier_id == "flagship_follow_up_outcome:targeted"
    assert (
        targeted.outcome_recommendation_disposition.value == "recommend_with_downgrade"
    )
    assert targeted.assay_worth_it is True
    assert any(
        "external execution parity" in reason
        for reason in targeted.missing_surface_reasons
    )


def test_outsider_packets_refuse_runtime_shortcut_backed_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.outsider_packets.build_runtime_flagship_proof_gate",
        lambda: SimpleNamespace(
            issues=(
                SimpleNamespace(
                    workflow_family="dda_import",
                    code="fake-helper-still-present-in-flagship-path",
                    detail="dda import still depends on a fake helper",
                ),
            )
        ),
    )

    packet = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.DDA)

    assert packet.complete_outsider_surface is False
    assert "dda import still depends on a fake helper" in packet.missing_surface_reasons


def test_outsider_packets_refuse_acceptance_sheet_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.outsider_packets.build_flagship_acceptance_sheet",
        lambda workflow_family: SimpleNamespace(
            earned_release_language=SimpleNamespace(value="review_grade_bounded"),
            claim_ahead_of_evidence=True,
            criteria=(
                SimpleNamespace(
                    passed=False,
                    dimension="calibration sanity",
                    observed_value="0",
                    required_relation=SimpleNamespace(value="at_least"),
                    required_value="1",
                ),
            ),
        ),
    )

    packet = build_flagship_outsider_review_packet(KnowledgeWorkflowFamily.DDA)

    assert packet.complete_outsider_surface is False
    assert any(
        "acceptance sheet says release language is ahead" in reason
        for reason in packet.missing_surface_reasons
    )
    assert any(
        "calibration sanity" in reason for reason in packet.missing_surface_reasons
    )
