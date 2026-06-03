# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""LFQ and multiplex benchmark review owners."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MultiplexNormalizationPolicy,
    QuantDecisionReadinessState,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_quant_decision_readiness_report,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.contracts.label_based import LabelBasedQuantBundle
from bijux_proteomics.quantification.provenance.review import (
    MultiplexChannelBalanceDiagnosticsReport,
    QuantReviewBundle,
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
    build_external_bundle,
    build_grounding_payload,
    build_public_claim_posture,
    build_vendor_caveat_ledger,
    grounding_summary_phrase,
    resolve_package_artifact_path,
    workflow_minimum_controls,
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


def build_lfq_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    build_quant_review_bundle: Callable[..., QuantReviewBundle],
    fingerprint_model: Callable[[JsonModel], str],
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build an LFQ benchmark review from checked-in feature evidence."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.LFQ:
        raise ValueError("LFQ benchmark review requires an LFQ workflow manifest")
    active_feature_path = feature_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_design_path = design_path or resolve_package_artifact_path(
        benchmark_manifest,
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
                benchmark_manifest.dataset_id,
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
        *benchmark_manifest.comparison_notes,
        *quant_review.caveats,
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
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, quant_review.artifact_bundle_hash),
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
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "LFQ benchmark review turns checked-in feature evidence into a reviewable quant bundle "
            "with missingness, QC, rollup limits, and decision-grade boundaries kept explicit; "
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
        comparison_notes=benchmark_manifest.comparison_notes,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )


def build_multiplex_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    build_label_based_quant_bundle: Callable[..., LabelBasedQuantBundle],
    build_multiplex_channel_balance_diagnostics_report: Callable[
        ..., MultiplexChannelBalanceDiagnosticsReport
    ],
    fingerprint_model: Callable[[JsonModel], str],
    feature_path: Path | None = None,
    design_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a multiplex benchmark review with explicit reporter-channel caveats."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.MULTIPLEX:
        raise ValueError(
            "multiplex benchmark review requires a multiplex workflow manifest"
        )
    active_feature_path = feature_path or resolve_package_artifact_path(
        benchmark_manifest,
        BenchmarkPackageArtifactKind.FEATURE_TABLE,
    )
    active_design_path = design_path or resolve_package_artifact_path(
        benchmark_manifest,
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
                benchmark_manifest.dataset_id,
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
        *benchmark_manifest.comparison_notes,
        *diagnostics.caveats,
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
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, bundle_artifact_id),
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
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "Multiplex benchmark review turns checked-in reporter evidence into a reviewable "
            "channel manifest with explicit missing-channel, imbalance, chemistry caveats, and decision-grade boundaries; "
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
        comparison_notes=benchmark_manifest.comparison_notes,
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )
