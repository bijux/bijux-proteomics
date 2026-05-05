# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.states import SupportState
from bijux_proteomics_intelligence import (
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
    build_lfq_benchmark_review,
    build_multiplex_benchmark_review,
    build_ptm_benchmark_review,
)
from bijux_proteomics_knowledge.references import KnowledgeWorkflowFamily


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_build_dda_benchmark_review_keeps_owner_surfaces_and_field_limits_visible() -> (
    None
):
    review = build_dda_benchmark_review(
        source_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "search_adapter_corpora"
            / "msfragger"
            / "msfragger_results.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.DDA
    assert review.ready_for_release_review is True
    assert "bijux-proteomics-intelligence: benchmark_reviews" in review.owner_surfaces
    assert any(
        claim.claim_id == "target_decoy_semantics"
        and claim.support_state is SupportState.SUPPORTED
        for claim in review.claim_summaries
    )
    assert review.external_reviewer_bundle.completeness_notes == ()
    assert "MSFragger fixture" in review.reviewer_summary


def test_build_dia_benchmark_review_keeps_capability_scope_explicit() -> None:
    review = build_dia_benchmark_review(
        source_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "search_adapter_corpora"
            / "spectronaut"
            / "spectronaut_report.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.DIA
    assert review.ready_for_release_review is True
    capability_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "dia_capability_scope"
    )
    assert capability_claim.support_state is SupportState.ADVISORY
    assert "vendor-library parity" in capability_claim.scientific_limits[0]
    assert "checked-in Spectronaut-style export" in review.reviewer_summary


def test_build_ptm_benchmark_review_keeps_ambiguity_explicit() -> None:
    review = build_ptm_benchmark_review(
        localization_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "ptm"
            / "localization_results.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.PTM
    ambiguity_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "site_ambiguity_visibility"
    )
    assert ambiguity_claim.support_state is SupportState.ADVISORY
    assert "ambiguous site groups" in ambiguity_claim.scientific_limits[0]
    assert "ambiguity" in review.reviewer_summary


def test_build_lfq_benchmark_review_keeps_qc_and_missingness_limits_visible() -> None:
    review = build_lfq_benchmark_review(
        feature_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "quant"
            / "study_scale_ms1_features.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.LFQ
    assert review.ready_for_release_review is True
    lfq_limit_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "qc_and_missingness_limits"
    )
    assert lfq_limit_claim.support_state is SupportState.ADVISORY
    assert review.external_reviewer_bundle.evidence_pointer_ids
    assert "missingness" in review.reviewer_summary


def test_build_multiplex_benchmark_review_keeps_channel_caveats_explicit() -> None:
    review = build_multiplex_benchmark_review(
        feature_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "quant"
            / "multiplex_ms1_features.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
    assert review.ready_for_release_review is True
    channel_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "channel_balance_caveats"
    )
    assert channel_claim.support_state is SupportState.ADVISORY
    assert "chemistry caveats" in channel_claim.scientific_limits[0]
    assert "missing-channel" in review.reviewer_summary
