# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted benchmark review owner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from bijux_proteomics.dia.benchmarks import (
    TargetedCalibrationStandardObservation,
    TargetedHandoffHonestyObservation,
    TargetedHeavyLightPairObservation,
    TargetedOutcomeReconciliationObservation,
    TargetedRawToReviewedBundleReport,
    TargetedWorkflowBenchmarkReport,
)
from bijux_proteomics.io.ingestion import parse_chromatogram_qc_table
from bijux_proteomics.lab.planning import (
    TargetedPlatformAssumptionInput,
    TargetedWorkflowBoundaryInput,
    TargetedWorkflowMethod,
    build_targeted_platform_support_matrix,
    evaluate_targeted_workflow_boundary,
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


def build_targeted_benchmark_review(
    *,
    benchmark_manifest: BenchmarkManifest,
    registry_entry: BenchmarkRegistryEntry,
    scientific_release_packet: ScientificReleasePacket,
    build_targeted_workflow_benchmark_report: Callable[
        ..., TargetedWorkflowBenchmarkReport
    ],
    build_targeted_raw_to_reviewed_bundle_report: Callable[
        ..., TargetedRawToReviewedBundleReport
    ],
    fingerprint_model: Callable[[JsonModel], str],
    qc_path: Path | None = None,
) -> WorkflowBenchmarkReview:
    """Build a targeted benchmark review with explicit control and vendor limits."""

    if benchmark_manifest.workflow_family is not KnowledgeWorkflowFamily.TARGETED:
        raise ValueError(
            "targeted benchmark review requires a targeted workflow manifest"
        )
    active_qc_path = qc_path or resolve_package_artifact_path(
        benchmark_manifest,
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
                benchmark_manifest.dataset_id,
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
        *benchmark_manifest.comparison_notes,
        "targeted support remains bounded by chromatogram QC, calibration, heavy/light pairing, and explicit vendor execution caveats.",
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
    external_bundle = build_external_bundle(
        bundle_id=f"{benchmark_manifest.benchmark_id}:external_review",
        workflow_family=benchmark_manifest.workflow_family,
        artifact_ids=(benchmark_manifest.dataset_id, artifact_id),
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
        benchmark_id=benchmark_manifest.benchmark_id,
        dataset_id=benchmark_manifest.dataset_id,
        workflow_family=benchmark_manifest.workflow_family,
        benchmark_authority_status=registry_entry.authority_status,
        title=benchmark_manifest.title,
        reviewer_summary=(
            "Targeted benchmark review keeps chromatogram QC, calibration standards, heavy/light pairing, transition interference, "
            "platform assumption scope, raw-to-reviewed handoff reconciliation, and Skyline or vendor execution parity caveats visible instead of inflating the workflow into strong vendor parity; "
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
        comparison_notes=benchmark_manifest.comparison_notes,
        vendor_caveat_ledger=vendor_caveats,
        external_reviewer_bundle=external_bundle,
        ready_for_release_review=all(
            claim.support_state is not SupportState.REFUSED for claim in claim_summaries
        ),
    )
