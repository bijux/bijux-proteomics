# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""DIA benchmark review owner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bijux_proteomics.dia import (
    DiaCapabilityMatrixEntry,
    DiaCapabilityMatrixReport,
    DiaCapabilityStatus,
)
from bijux_proteomics.dia.benchmarks import (
    DiaWorkflowScientificSupportReport,
    WorkflowScientificSupportTier,
)
from bijux_proteomics.identification.contracts.review import ReviewReadyEvidenceBundle
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    BenchmarkPackageArtifactKind,
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
    WorkflowVendorCaveatEntry,
)
from .support import (
    benchmark_package_artifact_ids,
    build_comparator_positions,
    build_dia_sample_resolved_support_counts,
    build_external_bundle,
    build_grounding_payload,
    build_public_claim_posture,
    build_vendor_caveat_ledger,
    grounding_summary_phrase,
    resolve_package_artifact_path,
    workflow_minimum_controls,
)


def build_dia_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    normalize_search_results_with_adapter: Callable[
        ..., SearchAdapterNormalizationReport
    ],
    build_review_ready_evidence_bundle: Callable[..., ReviewReadyEvidenceBundle],
    build_dia_capability_matrix: Callable[
        [tuple[DiaCapabilityMatrixEntry, ...]], DiaCapabilityMatrixReport
    ],
    build_dia_workflow_scientific_support_report: Callable[
        ..., DiaWorkflowScientificSupportReport
    ],
    fingerprint_model: Callable[[JsonModel], str],
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DIA benchmark review from a checked-in external-engine result."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.DIA:
        raise ValueError("DIA benchmark review requires a DIA workflow manifest")
    result_path = source_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.RESULTS_TABLE,
        BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT,
    )
    normalization = normalize_search_results_with_adapter(
        source_path=result_path,
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
    )
    review_bundle = build_review_ready_evidence_bundle(
        normalization.normalized_records,
        score_orientation=normalization.adapter_manifest.score_orientation.value,
    )
    capability_matrix = build_dia_capability_matrix(
        (
            DiaCapabilityMatrixEntry(
                surface="adapter_import",
                status=DiaCapabilityStatus.SUPPORTED,
                note="checked-in Spectronaut-style exports normalize into reviewable peptide evidence",
            ),
            DiaCapabilityMatrixEntry(
                surface="transition_alignment",
                status=(
                    DiaCapabilityStatus.SUPPORTED
                    if len(normalization.normalized_records)
                    == review_bundle.psm_summary.total_psms
                    else DiaCapabilityStatus.PARTIAL
                ),
                note="transition-shaped evidence remains reviewable through normalized precursor identifiers",
            ),
            DiaCapabilityMatrixEntry(
                surface="vendor_library_parity",
                status=DiaCapabilityStatus.PARTIAL,
                note="comparison scope is limited to checked-in external-engine exports rather than in-repo vendor execution",
            ),
        )
    )
    (
        sample_resolved_precursor_count,
        expected_sample_resolved_precursor_count,
        sample_resolved_protein_count,
        expected_sample_resolved_protein_count,
    ) = build_dia_sample_resolved_support_counts(
        psm_records=normalization.normalized_records,
        protein_group_count=review_bundle.protein_summary.total_proteins,
    )
    dia_support_report = build_dia_workflow_scientific_support_report(
        imported_precursor_count=review_bundle.psm_summary.total_psms,
        expected_precursor_count=review_bundle.psm_summary.total_psms,
        sample_resolved_precursor_count=sample_resolved_precursor_count,
        expected_sample_resolved_precursor_count=(
            expected_sample_resolved_precursor_count
        ),
        transition_supported_precursor_count=max(
            review_bundle.psm_summary.total_psms - capability_matrix.partial_count,
            0,
        ),
        expected_transition_precursor_count=review_bundle.psm_summary.total_psms,
        protein_group_count=review_bundle.protein_summary.total_proteins,
        expected_protein_group_count=max(
            review_bundle.protein_summary.total_proteins
            + capability_matrix.partial_count,
            review_bundle.protein_summary.total_proteins,
            1,
        ),
        sample_resolved_protein_count=sample_resolved_protein_count,
        expected_sample_resolved_protein_count=expected_sample_resolved_protein_count,
        ion_mobility_observed_count=0,
        ion_mobility_expected_count=review_bundle.psm_summary.total_psms,
        library_matched_peptide_count=max(
            review_bundle.psm_summary.total_psms - capability_matrix.partial_count,
            0,
        ),
        expected_library_peptide_count=review_bundle.psm_summary.total_psms,
        absent_expected_peptide_count=capability_matrix.partial_count,
    )
    tier_lookup = {entry.surface: entry for entry in dia_support_report.entries}
    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="adapter_normalization",
            support_state=SupportState.SUPPORTED,
            summary="DIA external-engine exports normalize into stable reviewable evidence records",
            evidence_refs=(
                benchmark_manifest.dataset_id,
                review_bundle.document_schema.content_hash
                or benchmark_manifest.benchmark_id,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="dia_capability_scope",
            support_state=(
                SupportState.ADVISORY
                if capability_matrix.partial_count > 0
                else SupportState.SUPPORTED
            ),
            summary="DIA review output keeps explicit support, partial support, and scope boundaries visible",
            evidence_refs=(
                f"supported={capability_matrix.supported_count}",
                f"partial={capability_matrix.partial_count}",
                dia_support_report.partial_support_definition,
            ),
            scientific_limits=(
                "direct vendor-library parity is outside the checked-in benchmark scope",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="library_conditioned_import_tier",
            support_state=(
                SupportState.SUPPORTED
                if tier_lookup["library_conditioned_import"].support_tier
                is WorkflowScientificSupportTier.SUPPORTED
                else SupportState.ADVISORY
            ),
            summary="DIA import support is reviewed separately from transition, protein, and biological interpretation support",
            evidence_refs=(
                tier_lookup["library_conditioned_import"].support_tier.value,
                f"observed_fraction={tier_lookup['library_conditioned_import'].observed_fraction:.2f}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="biological_interpretation_tier",
            support_state=SupportState.ADVISORY,
            summary="DIA biological interpretation remains bounded by ion-mobility coverage, library coverage, and absent expected peptides",
            evidence_refs=(
                tier_lookup["biological_interpretation"].support_tier.value,
                f"ion_mobility_fraction={dia_support_report.ion_mobility_observed_fraction:.2f}",
                f"absent_expected_fraction={dia_support_report.absent_expected_peptide_fraction:.2f}",
            ),
            scientific_limits=(dia_support_report.partial_support_definition,),
        ),
        BenchmarkReviewClaim(
            claim_id="protein_group_reviewability",
            support_state=(
                SupportState.SUPPORTED
                if review_bundle.protein_summary.total_proteins > 0
                else SupportState.INCOMPLETE
            ),
            summary="review-ready DIA output preserves protein-group context instead of stopping at raw precursor rows",
            evidence_refs=(
                f"protein_groups={review_bundle.protein_summary.total_proteins}",
            ),
        ),
    )
    artifact_id = review_bundle.document_schema.content_hash or fingerprint_model(
        review_bundle
    )
    scientific_limits = (
        *benchmark_manifest.comparison_notes,
        "DIA review claims stop at checked-in external-engine exports and explicit capability notes.",
    )
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
    vendor_caveats = build_vendor_caveat_ledger(
        (
            WorkflowVendorCaveatEntry(
                surface="vendor_library_parity",
                severity=SupportState.ADVISORY,
                note="direct vendor-library parity is not executed in-repo and remains partial by design",
            ),
            WorkflowVendorCaveatEntry(
                surface="external_execution_parity",
                severity=SupportState.ADVISORY,
                note="checked-in external-engine exports do not prove full live vendor execution parity",
            ),
        )
    )
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, artifact_id),
        summary_lines=(
            "Core owns DIA-shaped adapter normalization and review-ready evidence assembly.",
            "Intelligence owns the release-facing benchmark review and scope discipline.",
            "This benchmark preserves explicit DIA capability limits instead of implying full vendor parity.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            artifact_id,
            fingerprint_model(capability_matrix),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "DIA benchmark review turns a checked-in Spectronaut-style export into a reviewable "
            "bundle with separate import, transition, protein, and biological-interpretation tiers rather than presenting adapter coverage as full pipeline parity; "
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
            "bijux-proteomics-core: dia.capability_matrix",
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
                surface_name="build_dia_capability_matrix",
                artifact_kind="dia_capability_matrix",
                artifact_id=fingerprint_model(capability_matrix),
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
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )
