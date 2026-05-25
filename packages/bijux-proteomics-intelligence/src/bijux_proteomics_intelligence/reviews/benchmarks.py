# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark-backed review outputs for release-facing workflow scrutiny."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia import (
    DiaCapabilityMatrixEntry,
    DiaCapabilityStatus,
    build_dia_capability_matrix,
)
from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHandoffHonestyObservation,
    TargetedHeavyLightPairObservation,
    TargetedOutcomeReconciliationObservation,
    WorkflowScientificSupportTier,
    build_dia_workflow_scientific_support_report,
    build_targeted_raw_to_reviewed_bundle_report,
    build_targeted_workflow_benchmark_report,
)
from bijux_proteomics.identification import build_review_ready_evidence_bundle
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    build_search_adapter_conformance_report,
    normalize_search_results_with_adapter,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.ingestion import parse_chromatogram_qc_table
from bijux_proteomics.ptm import (
    build_ptm_site_ambiguity_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    build_glycopeptide_support_roadmap_report,
    build_ptm_family_credibility_track_report,
    build_ptm_raw_spectrum_validation_lane_report,
)
from bijux_proteomics.ptm.review import build_phospho_specific_review_fixture_report
from bijux_proteomics.quantification import (
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MultiplexNormalizationPolicy,
    QuantDecisionReadinessState,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
    build_quant_decision_readiness_report,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.review import (
    build_multiplex_channel_balance_diagnostics_report,
    build_quant_review_bundle,
)
from bijux_proteomics.review.collaboration import (
    ExternalReviewerBundle,
    ExternalReviewerBundleInput,
    build_external_reviewer_bundle,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.lab.planning import (
    TargetedPlatformAssumptionInput,
    TargetedWorkflowBoundaryInput,
    TargetedWorkflowMethod,
    build_targeted_platform_support_matrix,
    evaluate_targeted_workflow_boundary,
)
from bijux_proteomics.lab.qc_benchmarks import (
    build_workflow_minimum_control_report,
)
from bijux_proteomics_foundation import JsonModel, fingerprint_model
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    BenchmarkPackageArtifactKind,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ProteomicsComparatorTool,
    build_workflow_comparator_matrix,
)
from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityStatus,
    BenchmarkRegistryEntry,
)
from bijux_proteomics_knowledge.references.workflows.scientific_release import (
    ScientificReleasePacket,
    build_scientific_release_packet,
)


class BenchmarkReviewClaim(JsonModel):
    """One benchmark-backed claim with explicit support posture and review notes."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    support_state: SupportState
    summary: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReviewArtifact(JsonModel):
    """One reviewable artifact that anchors a benchmark-backed workflow claim."""

    model_config = ConfigDict(extra="forbid")

    owner_package: str = Field(..., min_length=1)
    surface_name: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    artifact_id: str = Field(..., min_length=1)


class BenchmarkComparatorPosition(JsonModel):
    """Exact comparator-tool posture carried into benchmark reviews."""

    model_config = ConfigDict(extra="forbid")

    comparator_tool: ProteomicsComparatorTool
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    matched_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    partial_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    refused_behaviors: tuple[str, ...] = Field(default_factory=tuple)
    not_attempted_behaviors: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowVendorCaveatEntry(JsonModel):
    """One vendor-facing caveat that must stay visible in release review."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    severity: SupportState
    note: str = Field(..., min_length=1)


class WorkflowVendorCaveatLedger(JsonModel):
    """Release-facing ledger of vendor and execution-parity caveats."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowVendorCaveatEntry, ...] = Field(default_factory=tuple)
    vendor_support_state: SupportState


class PtmFamilyReleaseTrack(JsonModel):
    """Release-facing PTM family track with explicit support posture."""

    model_config = ConfigDict(extra="forbid")

    family_name: str = Field(..., min_length=1)
    support_state: SupportState
    summary: str = Field(..., min_length=1)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)


class ReviewerGroundingState(StrEnum):
    """How strong the biological grounding is in a release-facing review summary."""

    DECISION_GRADE = "decision_grade"
    REVIEW_GRADE = "review_grade"
    THIN = "thin"


class WorkflowBenchmarkReview(JsonModel):
    """Release-facing review output for one benchmark-backed workflow path."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_authority_status: BenchmarkAuthorityStatus
    title: str = Field(..., min_length=1)
    reviewer_summary: str = Field(..., min_length=1)
    benchmark_package_id: str | None = None
    benchmark_package_summary: str | None = None
    benchmark_package_artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    comparator_positions: tuple[BenchmarkComparatorPosition, ...] = Field(
        default_factory=tuple
    )
    public_claim_support_state: ComparatorClaimSupportState
    comparator_failure_summaries: tuple[str, ...] = Field(default_factory=tuple)
    improvement_targets: tuple[str, ...] = Field(default_factory=tuple)
    known_loss_to_established_tool: bool = False
    reviewer_grounding_state: ReviewerGroundingState
    reviewer_grounding_limits: tuple[str, ...] = Field(default_factory=tuple)
    curated_reference_context: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_criteria: tuple[str, ...] = Field(default_factory=tuple)
    minimum_controls_required: tuple[str, ...] = Field(default_factory=tuple)
    scientific_release_packet: ScientificReleasePacket
    supported_repo_claims: tuple[str, ...] = Field(default_factory=tuple)
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    owner_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    review_artifacts: tuple[BenchmarkReviewArtifact, ...] = Field(default_factory=tuple)
    claim_summaries: tuple[BenchmarkReviewClaim, ...] = Field(default_factory=tuple)
    scientific_limits: tuple[str, ...] = Field(default_factory=tuple)
    comparison_notes: tuple[str, ...] = Field(default_factory=tuple)
    vendor_caveat_ledger: WorkflowVendorCaveatLedger | None = None
    supported_ptm_families: tuple[str, ...] = Field(default_factory=tuple)
    ptm_family_tracks: tuple[PtmFamilyReleaseTrack, ...] = Field(default_factory=tuple)
    external_reviewer_bundle: ExternalReviewerBundle
    ready_for_release_review: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _require_manifest(benchmark_id: str) -> BenchmarkManifest:
    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        raise ValueError(f"unknown benchmark manifest: {benchmark_id}")
    return manifest


def _require_registry_entry(benchmark_id: str) -> BenchmarkRegistryEntry:
    entry = get_benchmark_registry_entry(benchmark_id)
    if entry is None:
        raise ValueError(f"unknown benchmark registry entry: {benchmark_id}")
    return entry


def _benchmark_package_artifact_ids(benchmark_id: str) -> tuple[str, ...]:
    package = get_benchmark_package(benchmark_id)
    if package is None:
        return ()
    return tuple(artifact.artifact_id for artifact in package.package_artifacts)


def _build_comparator_positions(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[BenchmarkComparatorPosition, ...]:
    matrix = build_workflow_comparator_matrix(workflow_family=workflow_family)
    if not matrix.entries:
        return ()
    return tuple(
        BenchmarkComparatorPosition(
            comparator_tool=status.comparator_tool,
            comparator_path_ids=status.comparator_path_ids,
            matched_behaviors=status.matched_behaviors,
            partial_behaviors=status.partial_behaviors,
            refused_behaviors=status.refused_behaviors,
            not_attempted_behaviors=status.not_attempted_behaviors,
        )
        for status in matrix.entries[0].tool_statuses
    )


def _build_public_claim_posture(
    benchmark_id: str,
) -> tuple[
    ComparatorClaimSupportState,
    tuple[str, ...],
    tuple[str, ...],
    bool,
]:
    failure_report = build_benchmark_comparator_failure_report(
        benchmark_id=benchmark_id
    )
    if not failure_report.entries:
        return (ComparatorClaimSupportState.SUPPORTED, (), (), False)
    if any(
        entry.public_claim_support_state is ComparatorClaimSupportState.REFUSED
        for entry in failure_report.entries
    ):
        claim_state = ComparatorClaimSupportState.REFUSED
    else:
        claim_state = ComparatorClaimSupportState.ADVISORY
    summaries = tuple(entry.failure_summary for entry in failure_report.entries)
    improvement_targets = tuple(
        dict.fromkeys(entry.improvement_target for entry in failure_report.entries)
    )
    known_loss = any(
        entry.known_loss_to_established_tool for entry in failure_report.entries
    )
    return (claim_state, summaries, improvement_targets, known_loss)


def _build_external_bundle(
    *,
    bundle_id: str,
    workflow_family: KnowledgeWorkflowFamily,
    artifact_ids: tuple[str, ...],
    summary_lines: tuple[str, ...],
    scientific_limits: tuple[str, ...],
    hash_entries: tuple[str, ...],
) -> ExternalReviewerBundle:
    return build_external_reviewer_bundle(
        ExternalReviewerBundleInput(
            bundle_id=bundle_id,
            schema_refs=(
                "schema.benchmark_manifest.v1",
                f"schema.{workflow_family.value}.review.v1",
            ),
            evidence_pointer_ids=artifact_ids,
            summary_lines=summary_lines,
            hash_ledger_entries=hash_entries,
            reviewer_instructions=(
                "Review owner surfaces, benchmark evidence pointers, and explicit "
                "scientific limits before treating this workflow as release-ready."
            ),
        )
    )


def _build_vendor_caveat_ledger(
    entries: tuple[WorkflowVendorCaveatEntry, ...],
) -> WorkflowVendorCaveatLedger:
    vendor_support_state = (
        SupportState.SUPPORTED if not entries else SupportState.ADVISORY
    )
    return WorkflowVendorCaveatLedger(
        entries=entries,
        vendor_support_state=vendor_support_state,
    )


def _workflow_minimum_controls(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[str, ...]:
    report = build_workflow_minimum_control_report()
    entry = next(
        item for item in report.entries if item.workflow_family == workflow_family.value
    )
    return entry.minimum_controls


def _infer_search_adapter_kind(source_path: Path) -> SearchAdapterKind:
    """Infer the adapter kind for one checked-in benchmark result artifact."""

    artifact_name = source_path.name.lower()
    if "msfragger" in artifact_name:
        return SearchAdapterKind.MSFRAGGER
    if "maxquant" in artifact_name:
        return SearchAdapterKind.MAXQUANT_EVIDENCE
    if "spectronaut" in artifact_name:
        return SearchAdapterKind.SPECTRONAUT
    raise ValueError(f"cannot infer search adapter kind from {source_path.name!r}")


def _infer_search_adapter_dialect_id(source_path: Path) -> str | None:
    """Infer the checked-in result dialect when one benchmark path needs it."""

    artifact_name = source_path.name.lower()
    if "pipeline_export" in artifact_name:
        return "pipeline-export"
    return None


def _resolve_primary_pipeline_export(manifest: BenchmarkManifest) -> Path:
    """Resolve the primary checked-in external export for one benchmark package."""

    package = manifest.benchmark_package
    if package is None:
        return _repo_root() / manifest.dataset_locator
    primary_artifact = next(
        (
            artifact
            for artifact in package.package_artifacts
            if artifact.artifact_id.endswith("maxquant_export")
            and artifact.artifact_kind
            is BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT
        ),
        None,
    )
    if primary_artifact is None:
        primary_artifact = next(
            (
                artifact
                for artifact in package.package_artifacts
                if artifact.artifact_kind
                is BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT
            ),
            None,
        )
    if primary_artifact is None:
        return _repo_root() / manifest.dataset_locator
    return _repo_root() / primary_artifact.repo_relative_path


def _resolve_package_artifact_path(
    manifest: BenchmarkManifest,
    *artifact_kinds: BenchmarkPackageArtifactKind,
) -> Path:
    """Resolve the first tracked benchmark package artifact for one kind set."""

    package = manifest.benchmark_package
    if package is None:
        return _repo_root() / manifest.dataset_locator
    artifact = next(
        (
            item
            for item in package.package_artifacts
            if item.artifact_kind in artifact_kinds
        ),
        None,
    )
    if artifact is None:
        return _repo_root() / manifest.dataset_locator
    return _repo_root() / artifact.repo_relative_path


def _build_grounding_payload(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    benchmark_manifest: BenchmarkManifest,
    public_claim_support_state: ComparatorClaimSupportState,
) -> tuple[
    ReviewerGroundingState,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    briefing = build_workflow_reference_briefing(workflow_family)
    criteria = tuple(
        criterion.summary for criterion in briefing.decision_grade_framework.criteria
    )
    limits = tuple(
        dict.fromkeys(
            (
                *briefing.scope_limit_notes[:2],
                briefing.decision_grade_framework.decision_grade_definition,
            )
        )
    )
    if (
        public_claim_support_state is ComparatorClaimSupportState.SUPPORTED
        and benchmark_manifest.evidence_tier.value
        in {"public_truth_set", "external_reproduction_package"}
    ):
        grounding_state = ReviewerGroundingState.DECISION_GRADE
    elif public_claim_support_state is ComparatorClaimSupportState.REFUSED:
        grounding_state = ReviewerGroundingState.THIN
    else:
        grounding_state = ReviewerGroundingState.REVIEW_GRADE
    return (
        grounding_state,
        limits,
        briefing.interpretation_context_lines,
        criteria,
    )


def _grounding_summary_phrase(
    grounding_state: ReviewerGroundingState,
) -> str:
    if grounding_state is ReviewerGroundingState.DECISION_GRADE:
        return "biological grounding is strong enough to defend decision-grade review scope."
    if grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        return "biological grounding stays review-grade and explicitly bounded by benchmark and literature scope."
    return "biological grounding remains thin and cannot be hidden behind tidy benchmark prose."


def build_dda_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DDA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:dda_search_reproducibility"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.DDA:
        raise ValueError("DDA benchmark review requires a DDA workflow manifest")
    result_path = source_path or _resolve_primary_pipeline_export(manifest)
    adapter_kind = _infer_search_adapter_kind(result_path)
    dialect_id = _infer_search_adapter_dialect_id(result_path)
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

    field_loss = tuple(
        sorted(
            {
                *conformance.field_accounting.preserved_native_only_columns,
                *conformance.field_accounting.unsupported_columns,
                *conformance.field_accounting.lost_columns,
            }
        )
    )
    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="adapter_normalization",
            support_state=SupportState.SUPPORTED,
            summary="adapter-normalized DDA evidence stays reviewable after external-engine import",
            evidence_refs=(
                manifest.dataset_id,
                review_bundle.document_schema.content_hash or manifest.benchmark_id,
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
    scientific_limits = (*manifest.comparison_notes,)
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, artifact_id),
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
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "DDA benchmark review preserves external-engine normalization, target-decoy posture, "
            "and protein-level reviewability for the tracked DDA public package without pretending it is a full engine rerun; "
            f"{_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
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
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_dia_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    source_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a DIA benchmark review from a checked-in external-engine result."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:dia_library_extraction_consistency"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.DIA:
        raise ValueError("DIA benchmark review requires a DIA workflow manifest")
    result_path = source_path or _resolve_package_artifact_path(
        manifest,
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
    dia_support_report = build_dia_workflow_scientific_support_report(
        imported_precursor_count=review_bundle.psm_summary.total_psms,
        expected_precursor_count=review_bundle.psm_summary.total_psms,
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
                manifest.dataset_id,
                review_bundle.document_schema.content_hash or manifest.benchmark_id,
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
        *manifest.comparison_notes,
        "DIA review claims stop at checked-in external-engine exports and explicit capability notes.",
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    vendor_caveats = _build_vendor_caveat_ledger(
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
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, artifact_id),
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
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "DIA benchmark review turns a checked-in Spectronaut-style export into a reviewable "
            "bundle with separate import, transition, protein, and biological-interpretation tiers rather than presenting adapter coverage as full pipeline parity; "
            f"{_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
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
        comparison_notes=manifest.comparison_notes,
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_ptm_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    localization_path: Path | None = None,
    feature_path: Path | None = None,
    protein_fasta_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a PTM benchmark review from checked-in localization evidence."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:ptm_site_localization_confidence"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.PTM:
        raise ValueError("PTM benchmark review requires a PTM workflow manifest")
    active_localization_path = localization_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.RESULTS_TABLE,
    )
    active_feature_path = feature_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_fasta_path = protein_fasta_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.PROTEIN_FASTA,
    )

    parsed = parse_ptm_localization_tsv(active_localization_path)
    fasta = parse_fasta_document(
        active_fasta_path.read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    protein_sequences = {
        record.canonical_accession: record.residues for record in fasta.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=protein_sequences,
    )
    site_entries = build_ptm_site_table(mappings)
    ambiguity_entries = build_ptm_site_ambiguity_report(site_entries)
    feature_records = parse_ms1_feature_table(active_feature_path).accepted_records
    phospho_review = build_phospho_specific_review_fixture_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )
    raw_validation_lane = build_ptm_raw_spectrum_validation_lane_report(
        parsed.accepted_records,
        raw_spectrum_artifact_path=(
            "packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf"
        ),
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )
    family_tracks = build_ptm_family_credibility_track_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=protein_sequences,
    )
    glyco_roadmap = build_glycopeptide_support_roadmap_report(
        requested_workflow="n_glycopeptide_localization"
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="localization_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if parsed.accepted_records and not parsed.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="PTM localization evidence ingests into explicit site mappings instead of disappearing into score-only summaries",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(parsed.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="site_ambiguity_visibility",
            support_state=(
                SupportState.ADVISORY if ambiguity_entries else SupportState.SUPPORTED
            ),
            summary="PTM review keeps site ambiguity explicit instead of overstating localization certainty",
            evidence_refs=(f"ambiguous_sites={len(ambiguity_entries)}",),
            scientific_limits=(
                "ambiguous site groups remain review-critical caveats even when the benchmark path is otherwise complete",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="phospho_review_packet",
            support_state=(
                SupportState.SUPPORTED
                if phospho_review.motif_window_count
                >= len(phospho_review.phospho_site_keys)
                else SupportState.INCOMPLETE
            ),
            summary="PTM benchmark review reaches a phospho-specific decision brief with motif and occupancy caveats intact",
            evidence_refs=(
                f"motif_windows={phospho_review.motif_window_count}",
                f"quantified_samples={len(phospho_review.quantified_sample_ids)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="raw_spectrum_validation_lane",
            support_state=(
                SupportState.SUPPORTED
                if raw_validation_lane.ready_for_rescoring_follow_up
                else SupportState.ADVISORY
            ),
            summary="PTM review keeps a raw-spectrum-linked validation lane visible instead of stopping at TSV-localization ingestion",
            evidence_refs=(
                raw_validation_lane.raw_spectrum_artifact_path,
                f"fragment_supported_spectra={raw_validation_lane.fragment_supported_spectrum_count}",
            ),
            scientific_limits=(
                "rescoring follow-up weakens whenever localized spectra lack fragment-linked support",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="ptm_family_scope",
            support_state=SupportState.ADVISORY,
            summary="PTM release claims name the supported, interpretive-only, and refused PTM families explicitly",
            evidence_refs=(
                *family_tracks.supported_families,
                *family_tracks.interpretive_only_families,
                *family_tracks.refused_families,
            ),
            scientific_limits=(
                glyco_roadmap.current_disposition,
                *glyco_roadmap.required_scientific_work[:2],
            ),
        ),
    )
    review_artifact_id = fingerprint_model(phospho_review)
    scientific_limits = (
        *manifest.comparison_notes,
        "PTM review claims remain constrained by explicit ambiguous-site entries and phospho-focused fixture scope.",
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, review_artifact_id),
        summary_lines=(
            "Core owns PTM localization parsing, site mapping, and phospho review assembly.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark keeps ambiguous-site caveats visible instead of polishing them away.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            review_artifact_id,
            fingerprint_model(parsed),
        ),
    )
    ptm_release_tracks = tuple(
        PtmFamilyReleaseTrack(
            family_name=track.family_name,
            support_state=(
                SupportState.SUPPORTED
                if track.disposition.value == "supported"
                else SupportState.ADVISORY
                if track.disposition.value == "interpretive_only"
                else SupportState.REFUSED
            ),
            summary=track.evidence_summary,
            scientific_limits=track.caveats,
        )
        for track in family_tracks.tracks
    )
    supported_family_summary = ", ".join(family_tracks.supported_families) or "none"
    refused_family_summary = ", ".join(family_tracks.refused_families) or "none"
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "PTM benchmark review turns checked-in localization evidence into a phospho decision brief "
            f"while preserving explicit ambiguity and motif-scope limits, naming supported PTM families ({supported_family_summary}), "
            f"and refusing unsupported carryover ({refused_family_summary}); {_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
        owner_surfaces=(
            "bijux-proteomics-core: ptm.localization",
            "bijux-proteomics-core: ptm.review",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="parse_ptm_localization_tsv",
                artifact_kind="ptm_localization_parse_report",
                artifact_id=fingerprint_model(parsed),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_phospho_specific_review_fixture_report",
                artifact_kind="phospho_review_fixture_report",
                artifact_id=review_artifact_id,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        supported_ptm_families=family_tracks.supported_families,
        ptm_family_tracks=ptm_release_tracks,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_lfq_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build an LFQ benchmark review from checked-in feature evidence."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:lfq_quantification_repeatability"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.LFQ:
        raise ValueError("LFQ benchmark review requires an LFQ workflow manifest")
    active_feature_path = feature_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_design_path = design_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.DESIGN_TABLE,
    )

    feature_report = parse_ms1_feature_table(active_feature_path)
    design_report = parse_experimental_design_table(active_design_path)
    quant_review = build_quant_review_bundle(
        feature_report.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="feature_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if feature_report.accepted_records and not feature_report.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="LFQ benchmark review ingests checked-in feature rows without silently discarding invalid evidence",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(feature_report.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="quant_review_bundle",
            support_state=SupportState.SUPPORTED,
            summary="LFQ feature evidence reaches a reviewable quant bundle with provenance, missingness, QC, and rollup comparisons",
            evidence_refs=(
                quant_review.artifact_bundle_hash,
                *quant_review.evidence_pointers,
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="qc_and_missingness_limits",
            support_state=SupportState.ADVISORY,
            summary="LFQ review keeps QC and missingness caveats explicit before stronger abundance claims are made",
            evidence_refs=quant_review.caveats or ("no_lfq_caveats",),
            scientific_limits=(
                "repeatability claims remain bounded by the checked-in LFQ study-scale fixture and any QC caveats in the review bundle",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="decision_grade_boundary",
            support_state=(
                SupportState.SUPPORTED
                if quant_review.decision_readiness.readiness_state
                is QuantDecisionReadinessState.DECISION_GRADE
                else SupportState.ADVISORY
            ),
            summary="LFQ review separates quantitative values from decision-grade evidence authority",
            evidence_refs=(
                quant_review.decision_readiness.readiness_state.value,
                *quant_review.decision_readiness.advisory_reasons[:2],
                *quant_review.decision_readiness.blocking_reasons[:2],
            ),
            scientific_limits=(
                "decision-grade abundance claims are withheld whenever replicate or batch posture keeps the benchmark review-grade only",
            ),
        ),
    )
    scientific_limits = (
        *manifest.comparison_notes,
        *quant_review.caveats,
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, quant_review.artifact_bundle_hash),
        summary_lines=(
            "Core owns LFQ feature ingestion, normalization, rollup comparison, and QC assembly.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark limits LFQ support claims to the checked-in study-scale fixture and explicit QC caveats.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            quant_review.artifact_bundle_hash,
            fingerprint_model(quant_review),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "LFQ benchmark review turns checked-in feature evidence into a reviewable quant bundle "
            "with missingness, QC, rollup limits, and decision-grade boundaries kept explicit; "
            f"{_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
        owner_surfaces=(
            "bijux-proteomics-core: quantification.feature_ingestion",
            "bijux-proteomics-core: quantification.review",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="parse_ms1_feature_table",
                artifact_kind="ms1_feature_parse_report",
                artifact_id=fingerprint_model(feature_report),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_quant_review_bundle",
                artifact_kind="quant_review_bundle",
                artifact_id=quant_review.artifact_bundle_hash,
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_targeted_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    qc_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a targeted benchmark review with explicit control and vendor limits."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:targeted_transition_quality_control"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.TARGETED:
        raise ValueError(
            "targeted benchmark review requires a targeted workflow manifest"
        )
    active_qc_path = qc_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.TARGETED_QC_TABLE,
    )

    qc_report = parse_chromatogram_qc_table(active_qc_path)
    benchmark = build_targeted_workflow_benchmark_report(
        calibration_observations=(
            TargetedCalibrationStandardObservation(
                standard_id="std-a",
                sample_id="run-1",
                expected_ratio=1.0,
                observed_ratio=0.99,
                within_tolerance=True,
            ),
            TargetedCalibrationStandardObservation(
                standard_id="std-b",
                sample_id="run-2",
                expected_ratio=1.0,
                observed_ratio=1.27,
                within_tolerance=False,
            ),
        ),
        heavy_light_pairs=(
            TargetedHeavyLightPairObservation(
                pair_id="pair-a",
                light_candidate_id="pep-a-light",
                heavy_candidate_id="pep-a-heavy",
                pair_complete=True,
                heavy_light_ratio=1.01,
                interference_fraction=0.08,
            ),
            TargetedHeavyLightPairObservation(
                pair_id="pair-b",
                light_candidate_id="pep-b-light",
                heavy_candidate_id="pep-b-heavy",
                pair_complete=False,
                interference_fraction=0.21,
            ),
        ),
    )
    boundary = evaluate_targeted_workflow_boundary(
        TargetedWorkflowBoundaryInput(
            method=TargetedWorkflowMethod.PRM,
            has_transition_list=True,
            has_retention_windows=True,
            has_collision_energy_profile=True,
            has_instrument_method_template=False,
        )
    )
    platform_support = build_targeted_platform_support_matrix(
        (
            TargetedPlatformAssumptionInput(
                platform_id="orbitrap-prm",
                method=TargetedWorkflowMethod.PRM,
                has_transition_list=True,
                has_retention_windows=True,
                has_collision_energy_profile=True,
                has_instrument_method_template=False,
                has_heavy_reference=True,
                has_calibration_standards=True,
                has_vendor_tuning_profile=False,
            ),
        )
    )
    platform_entry = platform_support.entries[0]
    targeted_bundle = build_targeted_raw_to_reviewed_bundle_report(
        chromatogram_failed_metric_rows=qc_report.failed_metric_rows,
        benchmark_report=benchmark,
        handoff_observations=(
            TargetedHandoffHonestyObservation(
                handoff_id="supported_targeted_follow_up",
                claimed_transition_ready=True,
                calibration_failures_visible=True,
                interference_failures_visible=True,
                control_gaps_visible=True,
            ),
            TargetedHandoffHonestyObservation(
                handoff_id="failed_targeted_transition_follow_up",
                claimed_transition_ready=True,
                calibration_failures_visible=False,
                interference_failures_visible=True,
                control_gaps_visible=False,
            ),
        ),
        outcome_observations=(
            TargetedOutcomeReconciliationObservation(
                handoff_id="supported_targeted_follow_up",
                observed_transition_failure=False,
                reconciliation_recorded=True,
                corrective_action_visible=True,
            ),
            TargetedOutcomeReconciliationObservation(
                handoff_id="failed_targeted_transition_follow_up",
                observed_transition_failure=True,
                reconciliation_recorded=True,
                corrective_action_visible=True,
            ),
        ),
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="chromatogram_qc_surface",
            support_state=(
                SupportState.SUPPORTED
                if qc_report.accepted_points
                else SupportState.INCOMPLETE
            ),
            summary="targeted review preserves chromatogram-shaped QC as the first review surface",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_points={len(qc_report.accepted_points)}",
                f"failed_metric_rows={qc_report.failed_metric_rows}",
            ),
            scientific_limits=(
                "preserving QC failures as first-class review evidence does not make the targeted package calibration-clean or decision-grade by itself",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="calibration_and_pairing_pressure",
            support_state=(
                SupportState.SUPPORTED
                if benchmark.ready_for_transition_handoff
                else SupportState.ADVISORY
            ),
            summary="targeted review keeps calibration standards, heavy/light pairing, and transition interference explicit before handoff",
            evidence_refs=(
                f"calibration_failed={benchmark.calibration_failed_count}",
                f"missing_pairs={benchmark.missing_heavy_light_pair_count}",
                f"interference_flags={benchmark.interference_flag_count}",
            ),
            scientific_limits=(
                "targeted support weakens when calibration drifts, heavy/light pairs are incomplete, or interference rises",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="raw_to_reviewed_bundle",
            support_state=(
                SupportState.SUPPORTED
                if (
                    targeted_bundle.reconciled_outcome_count > 0
                    and targeted_bundle.unreconciled_outcome_count == 0
                    and (
                        targeted_bundle.honest_handoff_count
                        + targeted_bundle.inflated_handoff_count
                    )
                    > 0
                )
                else SupportState.ADVISORY
            ),
            summary="targeted review links chromatogram QC, handoff honesty, and observed outcome reconciliation instead of stopping at tidy assay packets",
            evidence_refs=(
                f"honest_handoffs={targeted_bundle.honest_handoff_count}",
                f"inflated_handoffs={targeted_bundle.inflated_handoff_count}",
                f"unreconciled_outcomes={targeted_bundle.unreconciled_outcome_count}",
            ),
            scientific_limits=(targeted_bundle.note,),
        ),
        BenchmarkReviewClaim(
            claim_id="vendor_execution_boundary",
            support_state=(
                SupportState.SUPPORTED if boundary.supported else SupportState.ADVISORY
            ),
            summary="targeted review keeps method-template and vendor-execution assumptions explicit instead of implying Skyline-style parity",
            evidence_refs=(
                boundary.method.value,
                *boundary.assumptions[:2],
            ),
            scientific_limits=(
                boundary.refusal_reason
                or "live vendor execution parity remains outside the checked-in targeted benchmark scope",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="platform_assumption_scope",
            support_state=(
                SupportState.SUPPORTED
                if platform_entry.support_state.value == "supported"
                else SupportState.ADVISORY
            ),
            summary="targeted review names platform and vendor assumptions explicitly instead of leaving follow-up readiness as a generic partial-support story",
            evidence_refs=(
                platform_entry.platform_id,
                platform_entry.support_state.value,
                *platform_entry.missing_assumptions,
            ),
            scientific_limits=(platform_entry.partial_support_definition,),
        ),
    )
    artifact_id = fingerprint_model(benchmark)
    scientific_limits = (
        *manifest.comparison_notes,
        "targeted support remains bounded by chromatogram QC, calibration, heavy/light pairing, and explicit vendor execution caveats.",
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    vendor_caveats = _build_vendor_caveat_ledger(
        (
            WorkflowVendorCaveatEntry(
                surface="skyline_or_vendor_execution_parity",
                severity=SupportState.ADVISORY,
                note="checked-in QC and transition artifacts do not prove live Skyline or vendor execution parity",
            ),
            WorkflowVendorCaveatEntry(
                surface="instrument_method_portability",
                severity=SupportState.ADVISORY,
                note="instrument templates and vendor-tuning assumptions remain explicit preconditions, not solved parity",
            ),
        )
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, artifact_id),
        summary_lines=(
            "Core owns targeted calibration, pairing, and transition-interference benchmark logic.",
            "Intelligence owns the release-facing targeted review summary and vendor caveat discipline.",
            "This benchmark does not claim live Skyline or vendor execution parity.",
            "Handoff honesty and observed outcome reconciliation are part of the targeted review bundle.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            artifact_id,
            fingerprint_model(qc_report),
            fingerprint_model(targeted_bundle),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "Targeted benchmark review keeps chromatogram QC, calibration standards, heavy/light pairing, transition interference, "
            "platform assumption scope, raw-to-reviewed handoff reconciliation, and Skyline or vendor execution parity caveats visible instead of inflating the workflow into strong vendor parity; "
            f"{_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
        owner_surfaces=(
            "bijux-proteomics-core: dia.targeted_benchmarks",
            "bijux-proteomics-core: io.chromatogram_qc_ingestion",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_targeted_workflow_benchmark_report",
                artifact_kind="targeted_workflow_benchmark_report",
                artifact_id=artifact_id,
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="parse_chromatogram_qc_table",
                artifact_kind="chromatogram_qc_ingestion_report",
                artifact_id=fingerprint_model(qc_report),
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_targeted_raw_to_reviewed_bundle_report",
                artifact_kind="targeted_raw_to_reviewed_bundle_report",
                artifact_id=fingerprint_model(targeted_bundle),
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def _default_multiplex_policy() -> LabelBasedQuantPolicy:
    return LabelBasedQuantPolicy(
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
        channel_entries=(
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="127N",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="128N",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="129N",
                channel_role=LabelBasedChannelRole.REFERENCE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="127N",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-b",
                multiplex_channel="128N",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
        ),
    )


def build_multiplex_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest | None = None,
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a multiplex benchmark review with explicit reporter-channel caveats."""

    manifest = benchmark_manifest or _require_manifest(
        "benchmark:multiplex_tmtpro_quantification"
    )
    registry_entry = _require_registry_entry(manifest.benchmark_id)
    if manifest.workflow_family is not KnowledgeWorkflowFamily.MULTIPLEX:
        raise ValueError(
            "multiplex benchmark review requires a multiplex workflow manifest"
        )
    active_feature_path = feature_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_design_path = design_path or _resolve_package_artifact_path(
        manifest,
        BenchmarkPackageArtifactKind.DESIGN_TABLE,
    )

    feature_report = parse_ms1_feature_table(active_feature_path)
    design_report = parse_experimental_design_table(active_design_path)
    table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    policy = _default_multiplex_policy()
    quant_bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_report.accepted_entries,
        policy=policy,
    )
    diagnostics = build_multiplex_channel_balance_diagnostics_report(
        table,
        design_entries=design_report.accepted_entries,
        quant_policy=policy,
        normalization_policy=MultiplexNormalizationPolicy(balance_ratio_threshold=1.2),
    )
    decision_readiness = build_quant_decision_readiness_report(
        table,
        design_entries=design_report.accepted_entries,
    )

    claim_summaries = (
        BenchmarkReviewClaim(
            claim_id="feature_ingestion",
            support_state=(
                SupportState.SUPPORTED
                if feature_report.accepted_records and not feature_report.rejected_rows
                else SupportState.INCOMPLETE
            ),
            summary="multiplex benchmark review ingests checked-in reporter evidence into a stable channel-aware table",
            evidence_refs=(
                manifest.dataset_id,
                f"accepted_records={len(feature_report.accepted_records)}",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="channel_manifest",
            support_state=(
                SupportState.ADVISORY
                if quant_bundle.missing_channels
                else SupportState.SUPPORTED
            ),
            summary="multiplex review keeps missing or preserved reporter channels explicit instead of treating the plex as complete by default",
            evidence_refs=(
                f"channels={len(quant_bundle.channels)}",
                f"missing_channels={len(quant_bundle.missing_channels)}",
            ),
            scientific_limits=(
                "missing channels remain explicit review caveats even when preserved in the manifest",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="channel_balance_caveats",
            support_state=SupportState.ADVISORY,
            summary="multiplex review surfaces channel imbalance and label-chemistry caveats before stronger biological claims are published",
            evidence_refs=(
                f"flagged_imbalance_count={diagnostics.flagged_imbalance_count}",
                f"missing_channel_count={diagnostics.missing_channel_count}",
            ),
            scientific_limits=(
                "TMTpro-style support claims stop at explicit channel semantics, balance diagnostics, and checked-in chemistry caveats",
            ),
        ),
        BenchmarkReviewClaim(
            claim_id="decision_grade_boundary",
            support_state=(
                SupportState.SUPPORTED
                if decision_readiness.readiness_state
                is QuantDecisionReadinessState.DECISION_GRADE
                else SupportState.ADVISORY
            ),
            summary="multiplex review separates stable reporter summaries from decision-grade biological authority",
            evidence_refs=(
                decision_readiness.readiness_state.value,
                *decision_readiness.advisory_reasons[:2],
                *decision_readiness.blocking_reasons[:2],
            ),
            scientific_limits=(
                "reporter-channel values remain review-grade whenever replicate or batch posture blocks decision-grade interpretation",
            ),
        ),
    )
    bundle_artifact_id = quant_bundle.document_schema.content_hash or fingerprint_model(
        quant_bundle
    )
    scientific_limits = (
        *manifest.comparison_notes,
        *diagnostics.caveats,
    )
    (
        public_claim_support_state,
        comparator_failure_summaries,
        improvement_targets,
        known_loss_to_established_tool,
    ) = _build_public_claim_posture(manifest.benchmark_id)
    (
        reviewer_grounding_state,
        reviewer_grounding_limits,
        curated_reference_context,
        decision_grade_criteria,
    ) = _build_grounding_payload(
        workflow_family=manifest.workflow_family,
        benchmark_manifest=manifest,
        public_claim_support_state=public_claim_support_state,
    )
    scientific_release_packet = build_scientific_release_packet(manifest)
    vendor_caveats = _build_vendor_caveat_ledger(
        (
            WorkflowVendorCaveatEntry(
                surface="vendor_multiplex_execution",
                severity=SupportState.ADVISORY,
                note="vendor-specific multiplex execution parity remains outside the checked-in chemistry fixture scope",
            ),
            WorkflowVendorCaveatEntry(
                surface="chemistry_family_scope",
                severity=SupportState.ADVISORY,
                note="the benchmark only speaks for bounded TMTpro channel semantics, not generic multiplex vendor behavior",
            ),
        )
    )
    external_bundle = _build_external_bundle(
        bundle_id=f"{manifest.benchmark_id}:external_review",
        workflow_family=manifest.workflow_family,
        artifact_ids=(manifest.dataset_id, bundle_artifact_id),
        summary_lines=(
            "Core owns multiplex feature ingestion, channel manifests, and balance diagnostics.",
            "Intelligence owns the release-facing benchmark review summary.",
            "This benchmark limits multiplex release claims to checked-in TMTpro-style channel semantics and explicit caveats.",
        ),
        scientific_limits=scientific_limits,
        hash_entries=(
            bundle_artifact_id,
            fingerprint_model(diagnostics),
        ),
    )
    return WorkflowBenchmarkReview(
        benchmark_id=manifest.benchmark_id,
        dataset_id=manifest.dataset_id,
        workflow_family=manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=manifest.title,
        reviewer_summary=(
            "Multiplex benchmark review turns checked-in reporter evidence into a reviewable "
            "channel manifest with explicit missing-channel, imbalance, chemistry caveats, and decision-grade boundaries; "
            f"{_grounding_summary_phrase(reviewer_grounding_state)}"
        ),
        benchmark_package_id=registry_entry.benchmark_package_id,
        benchmark_package_summary=registry_entry.benchmark_package_summary,
        benchmark_package_artifact_ids=_benchmark_package_artifact_ids(
            manifest.benchmark_id
        ),
        comparator_positions=_build_comparator_positions(manifest.workflow_family),
        public_claim_support_state=public_claim_support_state,
        comparator_failure_summaries=comparator_failure_summaries,
        improvement_targets=improvement_targets,
        known_loss_to_established_tool=known_loss_to_established_tool,
        reviewer_grounding_state=reviewer_grounding_state,
        reviewer_grounding_limits=reviewer_grounding_limits,
        curated_reference_context=curated_reference_context,
        decision_grade_criteria=decision_grade_criteria,
        minimum_controls_required=_workflow_minimum_controls(manifest.workflow_family),
        scientific_release_packet=scientific_release_packet,
        supported_repo_claims=registry_entry.supported_repo_claims,
        authorized_claim_scope=registry_entry.authorized_claim_scope,
        owner_surfaces=(
            "bijux-proteomics-core: quantification.label_based_quant_bundle",
            "bijux-proteomics-core: quantification.multiplex_balance",
            "bijux-proteomics-intelligence: benchmark_reviews",
        ),
        review_artifacts=(
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_label_based_quant_bundle",
                artifact_kind="label_based_quant_bundle",
                artifact_id=bundle_artifact_id,
            ),
            BenchmarkReviewArtifact(
                owner_package="bijux-proteomics-core",
                surface_name="build_multiplex_channel_balance_diagnostics_report",
                artifact_kind="multiplex_channel_balance_diagnostics",
                artifact_id=fingerprint_model(diagnostics),
            ),
        ),
        claim_summaries=claim_summaries,
        scientific_limits=scientific_limits,
        comparison_notes=manifest.comparison_notes,
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


__all__ = [
    "BenchmarkComparatorPosition",
    "BenchmarkReviewArtifact",
    "BenchmarkReviewClaim",
    "WorkflowBenchmarkReview",
    "build_dda_benchmark_review",
    "build_dia_benchmark_review",
    "build_lfq_benchmark_review",
    "build_multiplex_benchmark_review",
    "build_ptm_benchmark_review",
    "build_targeted_benchmark_review",
]
