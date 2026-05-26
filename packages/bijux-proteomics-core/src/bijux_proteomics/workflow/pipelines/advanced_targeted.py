# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced targeted-validation workflow execution over governed review surfaces."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.targeted import (
    TargetedPanelCandidateKind,
    TargetedResultImportReport,
    TargetedResultSourceKind,
    TargetedResultValidationPolicy,
    TargetedTransitionQcEntry,
    TargetedValidationAssayEvidenceEntry,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationEntry,
    TargetedValidationPanelAssayInput,
    TargetedResultValidationReport,
    TargetedValidationReasonCode,
    TargetedValidationVerdict,
    build_skyline_result_import_report,
    build_targeted_assay_qc_report,
    build_targeted_matrix_report,
    build_targeted_result_validation_report,
    build_transition_table_result_import_report,
    render_targeted_result_validation_evidence_tsv,
    render_targeted_result_validation_summary_tsv,
    render_targeted_result_validation_tsv,
)
from bijux_proteomics.workflow.targeted_review_workflow import (
    TargetedAssayQcWorkflowExportManifest,
    export_targeted_assay_qc_workflow_artifacts,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    artifact_name_map,
    build_rejected_evidence_entry,
    build_result_warning,
    render_result_rejected_evidence_tsv,
)
from bijux_proteomics.workflow.exports.artifact_layout import synchronize_workflow_artifact_layout
from bijux_proteomics_foundation import JsonModel


class TargetedValidationWorkflowConfig(JsonModel):
    """Config for the advanced targeted-validation workflow owner."""

    model_config = ConfigDict(extra="forbid")

    result_tsv_path: Path
    design_tsv_path: Path
    output_dir: Path
    discovery_claims: tuple[TargetedValidationDiscoveryClaimInput, ...] = Field(
        default_factory=tuple
    )
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...] = Field(
        default_factory=tuple
    )
    source_kind: TargetedResultSourceKind = TargetedResultSourceKind.SKYLINE_EXPORT
    case_condition: str = Field(..., min_length=1)
    control_condition: str = Field(..., min_length=1)
    minimum_reliable_replicates_per_condition: int = Field(default=2, ge=1)
    minimum_absolute_validation_log2_effect: float = Field(default=0.4, ge=0.0)
    flat_validation_log2_threshold: float = Field(default=0.2, ge=0.0)


class AdvancedTargetedAssayReliabilityStatus(StrEnum):
    """Candidate-level assay reliability posture across targeted follow-up assays."""

    RELIABLE = "reliable"
    MIXED = "mixed"
    UNRELIABLE = "unreliable"
    NOT_ASSAYED = "not_assayed"


class AdvancedTargetedWorkflowSummary(JsonModel):
    """Compact summary over one advanced targeted-validation workflow run."""

    model_config = ConfigDict(extra="forbid")

    observation_count: int = Field(..., ge=0)
    matrix_target_count: int = Field(..., ge=0)
    reliable_target_entry_count: int = Field(..., ge=0)
    unreliable_target_entry_count: int = Field(..., ge=0)
    flagged_coelution_target_entry_count: int = Field(..., ge=0)
    drift_flagged_fragment_ratio_observation_count: int = Field(..., ge=0)
    discovery_claim_count: int = Field(..., ge=0)
    confirmed_count: int = Field(..., ge=0)
    contradicted_count: int = Field(..., ge=0)
    inconclusive_count: int = Field(..., ge=0)
    evidence_card_count: int = Field(..., ge=0)


class AdvancedTargetedWorkflowArtifactPaths(JsonModel):
    """Advanced targeted-validation artifact paths written into the output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    targeted_assay_qc_workflow_manifest_json: str = Field(..., min_length=1)
    rejected_evidence_tsv: str = Field(..., min_length=1)
    import_summary_tsv: str = Field(..., min_length=1)
    observations_tsv: str = Field(..., min_length=1)
    matrix_summary_tsv: str = Field(..., min_length=1)
    matrix_targets_tsv: str = Field(..., min_length=1)
    matrix_samples_tsv: str = Field(..., min_length=1)
    matrix_retained_transitions_tsv: str = Field(..., min_length=1)
    matrix_excluded_transitions_tsv: str = Field(..., min_length=1)
    matrix_missingness_tsv: str = Field(..., min_length=1)
    assay_qc_summary_tsv: str = Field(..., min_length=1)
    assay_qc_targets_tsv: str = Field(..., min_length=1)
    assay_qc_transition_qc_tsv: str = Field(..., min_length=1)
    assay_qc_coelution_tsv: str = Field(..., min_length=1)
    assay_qc_transition_coelution_tsv: str = Field(..., min_length=1)
    assay_qc_fragment_ratios_tsv: str = Field(..., min_length=1)
    assay_qc_unreliable_targets_tsv: str = Field(..., min_length=1)
    validation_summary_tsv: str = Field(..., min_length=1)
    confirmed_validation_tsv: str = Field(..., min_length=1)
    contradicted_validation_tsv: str = Field(..., min_length=1)
    inconclusive_validation_tsv: str = Field(..., min_length=1)
    validation_evidence_tsv: str = Field(..., min_length=1)
    evidence_cards_tsv: str = Field(..., min_length=1)


class AdvancedTargetedWorkflowManifest(JsonModel):
    """Stable manifest over one advanced targeted-validation workflow directory."""

    model_config = ConfigDict(extra="forbid")

    summary: AdvancedTargetedWorkflowSummary
    artifacts: AdvancedTargetedWorkflowArtifactPaths
    targeted_assay_qc_workflow_manifest: TargetedAssayQcWorkflowExportManifest
    note: str = Field(..., min_length=1)


class AdvancedTargetedEvidenceCardEntry(JsonModel):
    """One candidate-level evidence card over discovery and targeted validation."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    validation_verdict: TargetedValidationVerdict
    assay_reliability_status: AdvancedTargetedAssayReliabilityStatus
    assay_entry_count: int = Field(..., ge=0)
    reliable_assay_count: int = Field(..., ge=0)
    unreliable_assay_count: int = Field(..., ge=0)
    confirmed_assay_count: int = Field(..., ge=0)
    contradicted_assay_count: int = Field(..., ge=0)
    inconclusive_assay_count: int = Field(..., ge=0)
    coelution_issue_count: int = Field(..., ge=0)
    ratio_drift_issue_count: int = Field(..., ge=0)
    validation_log2_effect: float | None = None
    discovery_effect_size: float | None = None
    reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class TargetedValidationWorkflowReport(BiologyResult):
    """Advanced targeted-validation workflow report with explicit claim-status cards."""

    model_config = ConfigDict(extra="forbid")

    import_report: TargetedResultImportReport
    targeted_assay_qc_workflow_manifest: TargetedAssayQcWorkflowExportManifest
    validation_report: TargetedResultValidationReport
    evidence_cards: tuple[AdvancedTargetedEvidenceCardEntry, ...] = Field(
        default_factory=tuple
    )
    summary: AdvancedTargetedWorkflowSummary
    manifest: AdvancedTargetedWorkflowManifest
    note: str = Field(..., min_length=1)


def run_targeted_validation_workflow(
    config: TargetedValidationWorkflowConfig,
) -> TargetedValidationWorkflowReport:
    """Run the advanced targeted-validation workflow and write one review directory."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    import_report = _build_import_report(config)
    design_report = parse_experimental_design_table(config.design_tsv_path)
    if design_report.rejected_rows:
        raise ValueError("design table contains rejected rows")
    design_entries = tuple(design_report.accepted_entries)

    matrix_report = build_targeted_matrix_report(import_report)
    assay_qc_report = build_targeted_assay_qc_report(import_report, design_entries)
    assay_qc_manifest = export_targeted_assay_qc_workflow_artifacts(
        import_report,
        matrix_report,
        assay_qc_report,
        output_dir,
    )
    assay_qc_manifest_path = output_dir / "targeted_assay_qc_workflow_manifest.json"
    assay_qc_manifest_path.write_text(
        assay_qc_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    validation_report = build_targeted_result_validation_report(
        config.discovery_claims,
        config.panel_assays,
        import_report,
        design_entries,
        policy=TargetedResultValidationPolicy(
            case_condition=config.case_condition,
            control_condition=config.control_condition,
            minimum_reliable_replicates_per_condition=(
                config.minimum_reliable_replicates_per_condition
            ),
            minimum_absolute_validation_log2_effect=(
                config.minimum_absolute_validation_log2_effect
            ),
            flat_validation_log2_threshold=config.flat_validation_log2_threshold,
        ),
    )
    evidence_cards = _build_evidence_cards(
        validation_report=validation_report,
        assay_qc_report=assay_qc_report,
    )

    validation_summary_name = "targeted_validation_summary.tsv"
    confirmed_name = "targeted_validation_confirmed.tsv"
    contradicted_name = "targeted_validation_contradicted.tsv"
    inconclusive_name = "targeted_validation_inconclusive.tsv"
    validation_evidence_name = "targeted_validation_evidence.tsv"
    evidence_card_name = "advanced_targeted_evidence_cards.tsv"
    rejected_evidence_name = "rejected_evidence.tsv"
    summary_name = "advanced_targeted_summary.tsv"

    write_output_table_tsv((output_dir / validation_summary_name), render_targeted_result_validation_summary_tsv(validation_report))
    write_output_table_tsv((output_dir / confirmed_name), render_targeted_result_validation_tsv(
            validation_report,
            TargetedValidationVerdict.CONFIRMED,
        ))
    write_output_table_tsv((output_dir / contradicted_name), render_targeted_result_validation_tsv(
            validation_report,
            TargetedValidationVerdict.CONTRADICTED,
        ))
    write_output_table_tsv((output_dir / inconclusive_name), render_targeted_result_validation_tsv(
            validation_report,
            TargetedValidationVerdict.INCONCLUSIVE,
        ))
    write_output_table_tsv((output_dir / validation_evidence_name), render_targeted_result_validation_evidence_tsv(validation_report))
    write_output_table_tsv((output_dir / evidence_card_name), render_advanced_targeted_evidence_cards_tsv(evidence_cards))
    write_output_table_tsv(
        (output_dir / rejected_evidence_name),
        render_result_rejected_evidence_tsv(
            _build_advanced_targeted_rejected_evidence(
                import_report=import_report,
                evidence_cards=evidence_cards,
                related_artifact=rejected_evidence_name,
            )
        ),
    )

    summary = AdvancedTargetedWorkflowSummary(
        observation_count=import_report.summary.observation_count,
        matrix_target_count=matrix_report.summary.target_count,
        reliable_target_entry_count=assay_qc_report.summary.reliable_target_entry_count,
        unreliable_target_entry_count=assay_qc_report.summary.unreliable_target_entry_count,
        flagged_coelution_target_entry_count=(
            assay_qc_report.summary.flagged_coelution_target_entry_count
        ),
        drift_flagged_fragment_ratio_observation_count=(
            assay_qc_report.summary.drift_flagged_fragment_ratio_observation_count
        ),
        discovery_claim_count=validation_report.summary.discovery_claim_count,
        confirmed_count=validation_report.summary.confirmed_count,
        contradicted_count=validation_report.summary.contradicted_count,
        inconclusive_count=validation_report.summary.inconclusive_count,
        evidence_card_count=len(evidence_cards),
    )
    write_output_table_tsv((output_dir / summary_name), render_advanced_targeted_workflow_summary_tsv(summary))

    manifest = AdvancedTargetedWorkflowManifest(
        summary=summary,
        artifacts=AdvancedTargetedWorkflowArtifactPaths(
            summary_tsv=summary_name,
            targeted_assay_qc_workflow_manifest_json=assay_qc_manifest_path.name,
            rejected_evidence_tsv=rejected_evidence_name,
            import_summary_tsv=assay_qc_manifest.artifacts.import_summary_tsv,
            observations_tsv=assay_qc_manifest.artifacts.observations_tsv,
            matrix_summary_tsv=assay_qc_manifest.artifacts.matrix_summary_tsv,
            matrix_targets_tsv=assay_qc_manifest.artifacts.matrix_targets_tsv,
            matrix_samples_tsv=assay_qc_manifest.artifacts.matrix_samples_tsv,
            matrix_retained_transitions_tsv=(
                assay_qc_manifest.artifacts.matrix_retained_transitions_tsv
            ),
            matrix_excluded_transitions_tsv=(
                assay_qc_manifest.artifacts.matrix_excluded_transitions_tsv
            ),
            matrix_missingness_tsv=assay_qc_manifest.artifacts.matrix_missingness_tsv,
            assay_qc_summary_tsv=assay_qc_manifest.artifacts.assay_qc_summary_tsv,
            assay_qc_targets_tsv=assay_qc_manifest.artifacts.assay_qc_targets_tsv,
            assay_qc_transition_qc_tsv=(
                assay_qc_manifest.artifacts.assay_qc_transition_qc_tsv
            ),
            assay_qc_coelution_tsv=assay_qc_manifest.artifacts.assay_qc_coelution_tsv,
            assay_qc_transition_coelution_tsv=(
                assay_qc_manifest.artifacts.assay_qc_transition_coelution_tsv
            ),
            assay_qc_fragment_ratios_tsv=(
                assay_qc_manifest.artifacts.assay_qc_fragment_ratios_tsv
            ),
            assay_qc_unreliable_targets_tsv=(
                assay_qc_manifest.artifacts.assay_qc_unreliable_targets_tsv
            ),
            validation_summary_tsv=validation_summary_name,
            confirmed_validation_tsv=confirmed_name,
            contradicted_validation_tsv=contradicted_name,
            inconclusive_validation_tsv=inconclusive_name,
            validation_evidence_tsv=validation_evidence_name,
            evidence_cards_tsv=evidence_card_name,
        ),
        targeted_assay_qc_workflow_manifest=assay_qc_manifest,
        note=(
            "advanced targeted validation preserves transition import, target matrix, "
            "coelution review, ratio drift review, assay reliability, discovery claim "
            "validation status, and evidence cards in one governed workflow surface"
        ),
    )
    manifest_path = output_dir / "advanced_targeted_workflow_manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
    synchronize_workflow_artifact_layout(
        output_dir,
        producer_function="run_targeted_validation_workflow",
    )

    return TargetedValidationWorkflowReport(
        import_report=import_report,
        targeted_assay_qc_workflow_manifest=assay_qc_manifest,
        validation_report=validation_report,
        evidence_cards=evidence_cards,
        summary=summary,
        manifest=manifest,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_advanced_targeted_warnings(summary=summary, manifest=manifest),
        rejected_evidence=_build_advanced_targeted_rejected_evidence(
            import_report=import_report,
            evidence_cards=evidence_cards,
            related_artifact=manifest.artifacts.rejected_evidence_tsv,
        ),
        note=(
            "advanced targeted validation composes transition import, target matrix, "
            "assay reliability, coelution, ratio drift, and discovery-claim validation "
            "without collapsing confirmed, contradicted, and inconclusive outcomes"
        ),
    )


def render_advanced_targeted_workflow_summary_tsv(
    summary: AdvancedTargetedWorkflowSummary,
) -> str:
    """Render one advanced targeted-validation workflow summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("observation_count", summary.observation_count),
        ("matrix_target_count", summary.matrix_target_count),
        ("reliable_target_entry_count", summary.reliable_target_entry_count),
        ("unreliable_target_entry_count", summary.unreliable_target_entry_count),
        (
            "flagged_coelution_target_entry_count",
            summary.flagged_coelution_target_entry_count,
        ),
        (
            "drift_flagged_fragment_ratio_observation_count",
            summary.drift_flagged_fragment_ratio_observation_count,
        ),
        ("discovery_claim_count", summary.discovery_claim_count),
        ("confirmed_count", summary.confirmed_count),
        ("contradicted_count", summary.contradicted_count),
        ("inconclusive_count", summary.inconclusive_count),
        ("evidence_card_count", summary.evidence_card_count),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_advanced_targeted_evidence_cards_tsv(
    entries: tuple[AdvancedTargetedEvidenceCardEntry, ...],
) -> str:
    """Render candidate-level advanced targeted evidence cards as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "validation_verdict",
            "assay_reliability_status",
            "assay_entry_count",
            "reliable_assay_count",
            "unreliable_assay_count",
            "confirmed_assay_count",
            "contradicted_assay_count",
            "inconclusive_assay_count",
            "coelution_issue_count",
            "ratio_drift_issue_count",
            "validation_log2_effect",
            "discovery_effect_size",
            "reason_codes",
            "note",
        )
    )
    for entry in sort_rows_by_fields(entries, "candidate_id"):
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                entry.validation_verdict.value,
                entry.assay_reliability_status.value,
                entry.assay_entry_count,
                entry.reliable_assay_count,
                entry.unreliable_assay_count,
                entry.confirmed_assay_count,
                entry.contradicted_assay_count,
                entry.inconclusive_assay_count,
                entry.coelution_issue_count,
                entry.ratio_drift_issue_count,
                "" if entry.validation_log2_effect is None else f"{entry.validation_log2_effect:g}",
                "" if entry.discovery_effect_size is None else f"{entry.discovery_effect_size:g}",
                ";".join(reason.value for reason in entry.reason_codes),
                entry.note,
            )
        )
    return handle.getvalue()


def _build_advanced_targeted_warnings(
    *,
    summary: AdvancedTargetedWorkflowSummary,
    manifest: AdvancedTargetedWorkflowManifest,
) -> tuple:
    warnings = []
    if summary.unreliable_target_entry_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_targeted:unreliable_targets",
                warning_code="unreliable_target_present",
                source_surface="advanced_targeted_workflow",
                message=(
                    "advanced targeted validation marked "
                    f"{summary.unreliable_target_entry_count} targets as unreliable"
                ),
                related_artifact=manifest.artifacts.assay_qc_unreliable_targets_tsv,
            )
        )
    if summary.contradicted_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_targeted:contradicted_claims",
                warning_code="contradicted_validation_present",
                source_surface="advanced_targeted_workflow",
                message=(
                    "advanced targeted validation contradicted "
                    f"{summary.contradicted_count} discovery claims"
                ),
                related_artifact=manifest.artifacts.contradicted_validation_tsv,
            )
        )
    if summary.inconclusive_count > 0:
        warnings.append(
            build_result_warning(
                warning_id="advanced_targeted:inconclusive_claims",
                warning_code="inconclusive_validation_present",
                source_surface="advanced_targeted_workflow",
                message=(
                    "advanced targeted validation left "
                    f"{summary.inconclusive_count} discovery claims inconclusive"
                ),
                related_artifact=manifest.artifacts.inconclusive_validation_tsv,
            )
        )
    return tuple(warnings)


def _build_advanced_targeted_rejected_evidence(
    *,
    import_report: TargetedResultImportReport,
    evidence_cards: tuple[AdvancedTargetedEvidenceCardEntry, ...],
    related_artifact: str,
) -> tuple:
    del import_report
    return tuple(
        build_rejected_evidence_entry(
            evidence_id=f"advanced_targeted:{card.candidate_id}",
            source_surface="advanced_targeted_workflow",
            reason_code=(
                "contradicted"
                if card.validation_verdict is TargetedValidationVerdict.CONTRADICTED
                else "inconclusive"
            ),
            message=card.note,
            related_artifact=related_artifact,
            entity_type="claim",
            entity_id=card.candidate_id,
        )
        for card in evidence_cards
        if card.validation_verdict is not TargetedValidationVerdict.CONFIRMED
        or card.assay_reliability_status
        is AdvancedTargetedAssayReliabilityStatus.UNRELIABLE
    )


def _build_import_report(
    config: TargetedValidationWorkflowConfig,
) -> TargetedResultImportReport:
    if config.source_kind is TargetedResultSourceKind.SKYLINE_EXPORT:
        return build_skyline_result_import_report(config.result_tsv_path)
    return build_transition_table_result_import_report(config.result_tsv_path)


def _build_evidence_cards(
    *,
    validation_report: TargetedResultValidationReport,
    assay_qc_report,
) -> tuple[AdvancedTargetedEvidenceCardEntry, ...]:
    assay_evidence_by_candidate: dict[str, list[TargetedValidationAssayEvidenceEntry]] = {}
    for entry in validation_report.assay_evidence:
        assay_evidence_by_candidate.setdefault(entry.candidate_id, []).append(entry)
    target_qc_by_target: dict[str, list[object]] = {}
    for entry in assay_qc_report.target_qc:
        target_qc_by_target.setdefault(entry.target_id, []).append(entry)
    transition_qc_by_target: dict[str, list[TargetedTransitionQcEntry]] = {}
    for entry in assay_qc_report.transition_qc:
        transition_qc_by_target.setdefault(entry.target_id, []).append(entry)

    cards: list[AdvancedTargetedEvidenceCardEntry] = []
    for validation_entry in validation_report.entries:
        candidate_assay_entries = tuple(
            sorted(
                assay_evidence_by_candidate.get(validation_entry.candidate_id, ()),
                key=lambda item: item.assay_entry_id,
            )
        )
        reliable_assay_count = 0
        coelution_issue_count = 0
        ratio_drift_issue_count = 0
        for assay_entry in candidate_assay_entries:
            if _assay_is_reliable(
                assay_entry,
                minimum_reliable_replicates=(
                    validation_report.policy.minimum_reliable_replicates_per_condition
                ),
            ):
                reliable_assay_count += 1
            if assay_entry.matched_target_id is None:
                continue
            target_qc_entries = target_qc_by_target.get(assay_entry.matched_target_id, ())
            transition_qc_entries = transition_qc_by_target.get(
                assay_entry.matched_target_id,
                (),
            )
            if any(
                "coeluting transitions" in reason
                for target_qc in target_qc_entries
                for reason in target_qc.reliability_reasons
            ) or any(entry.coelution_flagged for entry in transition_qc_entries):
                coelution_issue_count += 1
            if any(
                entry.ratio_drift_flagged or entry.ratio_unstable_transition_flagged
                for entry in transition_qc_entries
            ):
                ratio_drift_issue_count += 1

        assay_entry_count = len(candidate_assay_entries)
        unreliable_assay_count = assay_entry_count - reliable_assay_count
        reliability_status = _derive_assay_reliability_status(
            assay_entry_count=assay_entry_count,
            reliable_assay_count=reliable_assay_count,
        )
        cards.append(
            AdvancedTargetedEvidenceCardEntry(
                candidate_id=validation_entry.candidate_id,
                candidate_kind=validation_entry.candidate_kind,
                display_label=validation_entry.display_label,
                target_protein_ref=validation_entry.target_protein_ref,
                validation_verdict=validation_entry.verdict,
                assay_reliability_status=reliability_status,
                assay_entry_count=assay_entry_count,
                reliable_assay_count=reliable_assay_count,
                unreliable_assay_count=unreliable_assay_count,
                confirmed_assay_count=validation_entry.confirmed_assay_count,
                contradicted_assay_count=validation_entry.contradicted_assay_count,
                inconclusive_assay_count=validation_entry.inconclusive_assay_count,
                coelution_issue_count=coelution_issue_count,
                ratio_drift_issue_count=ratio_drift_issue_count,
                validation_log2_effect=validation_entry.validation_log2_effect,
                discovery_effect_size=validation_entry.discovery_effect_size,
                reason_codes=validation_entry.reason_codes,
                note=_build_evidence_card_note(
                    validation_entry=validation_entry,
                    reliability_status=reliability_status,
                    coelution_issue_count=coelution_issue_count,
                    ratio_drift_issue_count=ratio_drift_issue_count,
                ),
            )
        )
    return tuple(sort_rows_by_fields(tuple(cards), "candidate_id"))


def _assay_is_reliable(
    assay_entry: TargetedValidationAssayEvidenceEntry,
    *,
    minimum_reliable_replicates: int,
) -> bool:
    if assay_entry.matched_target_id is None:
        return False
    if assay_entry.matched_target_count != 1:
        return False
    if (
        assay_entry.case_reliable_sample_count < minimum_reliable_replicates
        or assay_entry.control_reliable_sample_count < minimum_reliable_replicates
    ):
        return False
    blocked_reasons = {
        TargetedValidationReasonCode.INSUFFICIENT_RELIABLE_REPLICATES,
        TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY,
        TargetedValidationReasonCode.AMBIGUOUS_TARGETED_RESULT_MAPPING,
        TargetedValidationReasonCode.NO_MATCHING_TARGETED_SIGNAL,
        TargetedValidationReasonCode.VALIDATION_SIGNAL_MISSING,
    }
    return not any(reason in blocked_reasons for reason in assay_entry.reason_codes)


def _derive_assay_reliability_status(
    *,
    assay_entry_count: int,
    reliable_assay_count: int,
) -> AdvancedTargetedAssayReliabilityStatus:
    if assay_entry_count == 0:
        return AdvancedTargetedAssayReliabilityStatus.NOT_ASSAYED
    if reliable_assay_count == 0:
        return AdvancedTargetedAssayReliabilityStatus.UNRELIABLE
    if reliable_assay_count == assay_entry_count:
        return AdvancedTargetedAssayReliabilityStatus.RELIABLE
    return AdvancedTargetedAssayReliabilityStatus.MIXED


def _build_evidence_card_note(
    *,
    validation_entry: TargetedValidationEntry,
    reliability_status: AdvancedTargetedAssayReliabilityStatus,
    coelution_issue_count: int,
    ratio_drift_issue_count: int,
) -> str:
    note = (
        "targeted validation "
        f"{validation_entry.verdict.value} the discovery claim with "
        f"{reliability_status.value} assay support"
    )
    if coelution_issue_count > 0 or ratio_drift_issue_count > 0:
        note += (
            f"; assay review preserved {coelution_issue_count} coelution concerns and "
            f"{ratio_drift_issue_count} ratio-drift concerns"
        )
    return note


__all__ = [
    "AdvancedTargetedAssayReliabilityStatus",
    "AdvancedTargetedEvidenceCardEntry",
    "AdvancedTargetedWorkflowArtifactPaths",
    "AdvancedTargetedWorkflowManifest",
    "AdvancedTargetedWorkflowSummary",
    "TargetedValidationWorkflowConfig",
    "TargetedValidationWorkflowReport",
    "render_advanced_targeted_evidence_cards_tsv",
    "render_advanced_targeted_workflow_summary_tsv",
    "run_targeted_validation_workflow",
]
