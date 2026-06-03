# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""DDA benchmark review owner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bijux_proteomics.identification.contracts.review import ReviewReadyEvidenceBundle
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterNormalizationReport,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterConformanceReport,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkRegistryEntry,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    ScientificReleasePacket,
)

from .models import (
    BenchmarkReviewArtifact,
    BenchmarkReviewClaim,
    WorkflowBenchmarkReview,
)
from .support import (
    benchmark_package_artifact_ids,
    build_comparator_positions,
    build_external_bundle,
    build_grounding_payload,
    build_public_claim_posture,
    grounding_summary_phrase,
    infer_search_adapter_dialect_id,
    infer_search_adapter_kind,
    resolve_primary_pipeline_export,
    workflow_minimum_controls,
)


def build_dda_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    normalize_search_results_with_adapter: Callable[
        ..., SearchAdapterNormalizationReport
    ],
    build_search_adapter_conformance_report: Callable[
        [SearchAdapterNormalizationReport], SearchAdapterConformanceReport
    ],
    build_review_ready_evidence_bundle: Callable[..., ReviewReadyEvidenceBundle],
    fingerprint_model: Callable[[JsonModel], str],
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DDA benchmark review from a checked-in external-engine result."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.DDA:
        raise ValueError("DDA benchmark review requires a DDA workflow manifest")
    result_path = source_path or resolve_primary_pipeline_export(benchmark_manifest)
    adapter_kind = infer_search_adapter_kind(result_path)
    dialect_id = infer_search_adapter_dialect_id(result_path)
    normalization = normalize_search_results_with_adapter(
        source_path=result_path,
        adapter_kind=adapter_kind,
        dialect_id=dialect_id or "default",
    )
    conformance = build_search_adapter_conformance_report(normalization)
    review_bundle = build_review_ready_evidence_bundle(
        normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
    )

    field_accounting = conformance.field_accounting
    field_loss = tuple(
        sorted(
            {
                *field_accounting.preserved_native_only_columns,
                *field_accounting.unsupported_columns,
                *field_accounting.lost_columns,
            }
        )
    )
    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="adapter_normalization",
            support_state=SupportState.SUPPORTED,
            summary="adapter-normalized DDA evidence stays reviewable after external-engine import",
            evidence_refs=(
                benchmark_manifest.dataset_id,
                review_bundle.document_schema.content_hash
                or benchmark_manifest.benchmark_id,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="target_decoy_semantics",
            support_state=(
                SupportState.SUPPORTED
                if review_bundle.psm_summary.decoy_psms > 0
                else SupportState.AMBIGUOUS
            ),
            summary="review bundle keeps target-decoy evidence visible instead of flattening confidence posture",
            evidence_refs=(f"decoy_psms={review_bundle.psm_summary.decoy_psms}",),
            scientific_limits=(
                "review support weakens if decoy evidence disappears from the normalized result set",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="field_loss_accounting",
            support_state=(
                SupportState.ADVISORY if field_loss else SupportState.SUPPORTED
            ),
            summary="adapter review keeps any preserved-native or unsupported search columns explicit",
            evidence_refs=field_loss or ("no_extra_field_loss",),
            scientific_limits=(
                "native engine-specific columns remain comparison scope notes, not portable scientific claims",
            ),
        ),
    )
    artifact_id = review_bundle.document_schema.content_hash or fingerprint_model(
        review_bundle
    )
    scientific_limits = benchmark_manifest.comparison_notes
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = build_public_claim_posture(benchmark_manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = build_grounding_payload(
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_manifest=benchmark_manifest,
        public_claim_support_state=public_claim_support_state,
    )
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, artifact_id),
        summary_lines=(
            "Core owns DDA parsing, adapter normalization, and the tracked public package boundary.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark is limited to the tracked DDA public package, its primary imported export, and explicit cross-engine comparison notes.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            artifact_id,
            fingerprint_model(normalization),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "DDA benchmark review preserves external-engine normalization, target-decoy posture, "
            "and protein-level reviewability for the tracked DDA public package without pretending it is a full engine rerun; "
            f"{grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=benchmark_package_artifact_ids(
            benchmark_manifest.benchmark_id
        ),
        comparator_positions=build_comparator_positions(
            benchmark_manifest.workflow_family
        ),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=workflow_minimum_controls(
            benchmark_manifest.workflow_family
        ),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
        owner_surfaces=(
            "bijux-proteomics-core: identification.search_adapters",
            "bijux-proteomics-core: identification.review_ready_evidence_bundle",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="normalize_search_results_with_adapter",
                artifact_kind="search_adapter_normalization_report",
                artifact_id=fingerprint_model(normalization),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_review_ready_evidence_bundle",
                artifact_kind="review_ready_evidence_bundle",
                artifact_id=artifact_id,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=benchmark_manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )
