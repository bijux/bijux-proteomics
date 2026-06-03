# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_proteomics.dia.benchmarks import (
    DiaWorkflowScientificSupportReport,
)
from bijux_proteomics.dia.benchmarks import (
    build_dia_workflow_scientific_support_report as build_core_dia_workflow_scientific_support_report,
)
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterNormalizationReport,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
import bijux_proteomics_intelligence.reviews.benchmarks as benchmark_reviews
from bijux_proteomics_intelligence.reviews.benchmarks import (
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
    build_lfq_benchmark_review,
    build_multiplex_benchmark_review,
    build_ptm_benchmark_review,
    build_targeted_benchmark_review,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityStatus,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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
    assert review.benchmark_authority_status is BenchmarkAuthorityStatus.ACTIVE
    assert review.benchmark_package_id is not None
    assert review.benchmark_package_artifact_ids
    assert review.public_claim_support_state.value == "advisory"
    assert review.comparator_failure_summaries
    assert any(
        position.comparator_tool.value == "msfragger" and position.matched_behaviors
        for position in review.comparator_positions
    )
    assert review.supported_repo_claims
    assert review.ready_for_release_review is True
    assert review.curated_reference_context
    assert review.decision_grade_criteria
    assert review.minimum_controls_required
    assert review.scientific_release_packet.threshold_evidence.entries
    assert review.scientific_release_packet.failure_trap_report.entries
    assert "bijux-proteomics-intelligence: benchmark_reviews" in review.owner_surfaces
    assert any(
        claim.claim_id == "target_decoy_semantics"
        and claim.support_state is SupportState.SUPPORTED
        for claim in review.claim_summaries
    )
    assert review.external_reviewer_bundle.completeness_notes == ()
    assert "tracked DDA public package" in review.reviewer_summary


def test_build_dda_benchmark_review_defaults_to_public_package_primary_export() -> None:
    review = build_dda_benchmark_review()

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.DDA
    assert review.benchmark_package_id == "benchmark_package:dda_reviewable_run"
    assert any(
        claim.claim_id == "target_decoy_semantics"
        and claim.support_state is SupportState.SUPPORTED
        for claim in review.claim_summaries
    )
    assert "tracked DDA public package" in review.reviewer_summary


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
    assert review.benchmark_package_id is not None
    assert review.public_claim_support_state.value == "advisory"
    assert any(
        position.comparator_tool.value == "spectronaut" and position.partial_behaviors
        for position in review.comparator_positions
    )
    assert any(
        position.comparator_tool.value == "diann" and position.matched_behaviors
        for position in review.comparator_positions
    )
    assert review.ready_for_release_review is True
    capability_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "dia_capability_scope"
    )
    assert capability_claim.support_state is SupportState.ADVISORY
    assert "vendor-library parity" in capability_claim.scientific_limits[0]
    interpretation_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "biological_interpretation_tier"
    )
    assert interpretation_claim.support_state is SupportState.ADVISORY
    assert "partial DIA support means" in interpretation_claim.scientific_limits[0]
    assert "biological-interpretation tiers" in review.reviewer_summary
    assert review.reviewer_grounding_state.value == "review_grade"
    assert (
        review.scientific_release_packet.benchmark_metric_priorities.entries[0].weight
        == 5
    )


def test_build_dia_benchmark_review_uses_aggregate_fallback_without_run_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_arguments: dict[str, int] = {}

    def _capture_support_arguments(
        **kwargs: int,
    ) -> DiaWorkflowScientificSupportReport:
        observed_arguments.update(kwargs)
        return build_core_dia_workflow_scientific_support_report(**kwargs)

    benchmark_path = (
        _repo_root()
        / "packages"
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "search_adapter_corpora"
        / "spectronaut"
        / "spectronaut_report.tsv"
    )
    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.benchmarks.build_dia_workflow_scientific_support_report",
        _capture_support_arguments,
    )
    review = benchmark_reviews.build_dia_benchmark_review(source_path=benchmark_path)

    assert review.workflow_family is KnowledgeWorkflowFamily.DIA
    assert observed_arguments["sample_resolved_precursor_count"] == 3
    assert observed_arguments["expected_sample_resolved_precursor_count"] == 3
    assert observed_arguments["sample_resolved_protein_count"] == 4
    assert observed_arguments["expected_sample_resolved_protein_count"] == 4


def test_build_dia_benchmark_review_uses_run_resolved_counts_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_arguments: dict[str, int] = {}

    def _capture_support_arguments(
        **kwargs: int,
    ) -> DiaWorkflowScientificSupportReport:
        observed_arguments.update(kwargs)
        return build_core_dia_workflow_scientific_support_report(**kwargs)

    def _normalize_synthetic_records(**_: object) -> SearchAdapterNormalizationReport:
        return cast(
            SearchAdapterNormalizationReport,
            SimpleNamespace(
                normalized_records=synthetic_records,
                adapter_manifest=SimpleNamespace(
                    score_orientation=SimpleNamespace(value="higher_better")
                ),
            ),
        )

    def _synthetic_fingerprint(_: JsonModel) -> str:
        return "synthetic-normalization"

    synthetic_records = (
        PsmRecord(
            run_id="run-a",
            spectrum_id="spec-1",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=42.0,
            protein_refs=("P11111",),
        ),
        PsmRecord(
            run_id="run-a",
            spectrum_id="spec-2",
            peptide="SEQUENCE",
            canonical_peptide="SEQUENCE",
            charge=3,
            score=43.0,
            protein_refs=("P22222",),
        ),
        PsmRecord(
            run_id="run-b",
            spectrum_id="spec-3",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=41.0,
            protein_refs=("P11111",),
        ),
    )

    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.benchmarks.normalize_search_results_with_adapter",
        _normalize_synthetic_records,
    )
    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.benchmarks.build_dia_workflow_scientific_support_report",
        _capture_support_arguments,
    )
    monkeypatch.setattr(
        "bijux_proteomics_intelligence.reviews.benchmarks.fingerprint_model",
        _synthetic_fingerprint,
    )
    review = benchmark_reviews.build_dia_benchmark_review(
        source_path=Path("synthetic_spectronaut.tsv")
    )

    assert review.workflow_family is KnowledgeWorkflowFamily.DIA
    assert observed_arguments["sample_resolved_precursor_count"] == 3
    assert observed_arguments["expected_sample_resolved_precursor_count"] == 3
    assert observed_arguments["sample_resolved_protein_count"] == 3
    assert observed_arguments["expected_sample_resolved_protein_count"] == 3


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
    assert review.public_claim_support_state.value == "advisory"
    assert review.improvement_targets
    assert any(
        position.comparator_tool.value == "maxquant" and position.refused_behaviors
        for position in review.comparator_positions
    )
    ambiguity_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "site_ambiguity_visibility"
    )
    assert ambiguity_claim.support_state is SupportState.ADVISORY
    assert "ambiguous site groups" in ambiguity_claim.scientific_limits[0]
    assert "ambiguity" in review.reviewer_summary
    assert review.supported_ptm_families == ("acetylation", "ubiquitin_remnant")
    assert any(
        track.family_name == "glyco_adjacent" for track in review.ptm_family_tracks
    )
    assert review.curated_reference_context
    assert review.decision_grade_criteria
    assert review.scientific_release_packet.flagship_reproducibility_pack.artifact_ids


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
    assert review.benchmark_package_id is not None
    assert review.public_claim_support_state.value == "advisory"
    assert any(
        position.comparator_tool.value == "maxquant" and position.partial_behaviors
        for position in review.comparator_positions
    )
    assert review.ready_for_release_review is True
    assert review.authorized_claim_scope
    lfq_limit_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "qc_and_missingness_limits"
    )
    assert lfq_limit_claim.support_state is SupportState.ADVISORY
    decision_boundary_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "decision_grade_boundary"
    )
    assert decision_boundary_claim.evidence_refs
    assert review.external_reviewer_bundle.evidence_pointer_ids
    assert "missingness" in review.reviewer_summary
    assert review.reviewer_grounding_state.value == "review_grade"
    assert (
        review.scientific_release_packet.graduation_state.value
        == "outsider_trust_ready"
    )


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
    assert review.benchmark_package_id is not None
    assert review.public_claim_support_state.value == "refused"
    assert any(
        position.comparator_tool.value == "maxquant"
        and position.not_attempted_behaviors
        for position in review.comparator_positions
    )
    assert review.ready_for_release_review is True
    assert review.supported_repo_claims
    channel_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "channel_balance_caveats"
    )
    assert channel_claim.support_state is SupportState.ADVISORY
    decision_boundary_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "decision_grade_boundary"
    )
    assert decision_boundary_claim.evidence_refs
    assert "chemistry caveats" in channel_claim.scientific_limits[0]
    assert "missing-channel" in review.reviewer_summary
    assert review.vendor_caveat_ledger is not None
    assert review.vendor_caveat_ledger.vendor_support_state is SupportState.ADVISORY
    assert review.reviewer_grounding_state.value == "thin"
    assert review.scientific_release_packet.evidence_quality_gate_passed is False


def test_build_targeted_benchmark_review_keeps_vendor_and_control_limits_visible() -> (
    None
):
    review = build_targeted_benchmark_review(
        qc_path=(
            _repo_root()
            / "packages"
            / "bijux-proteomics-core"
            / "tests"
            / "fixtures"
            / "formats"
            / "targeted_benchmark_qc.tsv"
        )
    )

    assert isinstance(review, WorkflowBenchmarkReview)
    assert review.workflow_family is KnowledgeWorkflowFamily.TARGETED
    assert review.public_claim_support_state.value == "advisory"
    assert review.vendor_caveat_ledger is not None
    assert review.vendor_caveat_ledger.vendor_support_state is SupportState.ADVISORY
    vendor_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "vendor_execution_boundary"
    )
    platform_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "platform_assumption_scope"
    )
    assert vendor_claim.scientific_limits
    assert platform_claim.support_state is SupportState.ADVISORY
    assert "partial targeted support means" in platform_claim.scientific_limits[0]
    raw_to_reviewed_claim = next(
        claim
        for claim in review.claim_summaries
        if claim.claim_id == "raw_to_reviewed_bundle"
    )
    assert raw_to_reviewed_claim.support_state is SupportState.SUPPORTED
    assert review.minimum_controls_required == (
        "blank",
        "heavy_reference",
        "calibration_standard",
    )
    assert review.reviewer_grounding_state.value == "review_grade"
    assert any(
        artifact.artifact_kind == "targeted_raw_to_reviewed_bundle_report"
        for artifact in review.review_artifacts
    )
    assert "Skyline or vendor execution parity" in review.reviewer_summary
    assert "biological grounding stays review-grade" in review.reviewer_summary
    assert review.scientific_release_packet.threshold_evidence.entries
    assert review.scientific_release_packet.hostile_reviewer_checklist.items
    assert review.scientific_release_packet.science_tables.tables
