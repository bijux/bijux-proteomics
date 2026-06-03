# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-owned discovery-to-assay design over governed targeted surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceEntry
from bijux_proteomics.io import SpectralLibraryEntry
from bijux_proteomics.sequences import (
    NormalizedProteinRecord,
    PeptideChemicalLiabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted import (
    DiscoveryTargetProteinEntry,
    DiscoveryTargetedPeptideSelectionEntry,
    DiscoveryTargetedPeptideSelectionReport,
    TargetedAssayInterferenceReport,
    TargetedPanelAssayInput,
    TargetedPanelAssayEntry,
    TargetedPanelBiomarkerCandidateInput,
    TargetedPanelCandidateKind,
    TargetedPanelDesignReport,
    TargetedPanelSelectedPeptideInput,
    TargetedPanelTransitionEntry,
    TargetedPanelTransitionInput,
    TargetedTransitionSelectionPeptideEntry,
    TargetedTransitionSelectionReport,
    ValidationEvidenceCardReport,
    ValidationEvidenceDiscoveryInput,
    ValidationEvidenceOmittedCandidateInput,
    ValidationEvidencePanelAssayInput,
    build_discovery_targeted_peptide_selection_report,
    build_targeted_assay_interference_report,
    build_targeted_panel_design_report,
    build_targeted_transition_selection_report,
    build_validation_evidence_card_report,
    render_discovery_targeted_peptide_selection_rejected_tsv,
    render_discovery_targeted_peptide_selection_selected_tsv,
    render_validation_evidence_card_assay_tsv,
    render_validation_evidence_card_summary_tsv,
    render_validation_evidence_card_tsv,
    render_validation_evidence_card_warning_tsv,
    render_targeted_panel_design_assay_tsv,
    render_targeted_panel_design_omitted_candidate_tsv,
    render_targeted_panel_design_panel_tsv,
    render_targeted_transition_selection_rejected_tsv,
    render_targeted_transition_selection_selected_tsv,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics.workflow.result_types import (
    RejectedEvidenceEntry,
    ResultWarningEntry,
    WorkflowResult,
    artifact_name_map,
    build_rejected_evidence_entry,
    build_result_warning,
)


class DiscoveryAssaySourceResult(JsonModel):
    """Discovery-side evidence surfaces used for assay design."""

    model_config = ConfigDict(extra="forbid")

    peptide_evidence_entries: tuple[PeptideEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    protein_records: tuple[NormalizedProteinRecord, ...] = Field(default_factory=tuple)
    spectral_library_entries: tuple[SpectralLibraryEntry, ...] = Field(
        default_factory=tuple
    )


class DiscoveryAssayTargetInput(JsonModel):
    """One discovery-ranked target carried into assay design."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    weighted_evidence_total: float | None = Field(default=None, ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    support_count: int = Field(default=0, ge=0)
    annotation_labels: tuple[str, ...] = Field(default_factory=tuple)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(
        default="discovery-ranked biomarker candidate prepared for assay planning",
        min_length=1,
    )
    discovery_peptides: tuple[str, ...] = Field(default_factory=tuple)


class DiscoveryAssayFeasibilityStatus(StrEnum):
    """Stable feasibility outcomes for discovery-ranked assay targets."""

    ASSAY_READY = "assay_ready"
    PEPTIDE_UNAVAILABLE = "peptide_unavailable"
    TRANSITION_LIMITED = "transition_limited"
    SITE_SPECIFIC_FOLLOW_UP_REQUIRED = "site_specific_follow_up_required"


class DiscoveryAssayTargetEntry(JsonModel):
    """One discovery target with explicit peptide and assay feasibility accounting."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    acceptable_peptide_count: int = Field(..., ge=0)
    transition_supported_peptide_count: int = Field(..., ge=0)
    retained_assay_count: int = Field(..., ge=0)
    panel_transition_count: int = Field(..., ge=0)
    expected_retention_time_available: bool
    best_peptide_sequence: str | None = None
    best_uniqueness_class: PeptideUniquenessClass | None = None
    best_liability_tier: PeptideChemicalLiabilityTier | None = None
    liability_codes: tuple[str, ...] = Field(default_factory=tuple)
    assay_feasibility: DiscoveryAssayFeasibilityStatus
    note: str = Field(..., min_length=1)


class DiscoveryToAssaySummary(JsonModel):
    """Compact accounting over one discovery-to-assay design pass."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    protein_target_count: int = Field(..., ge=0)
    ptm_site_target_count: int = Field(..., ge=0)
    target_with_acceptable_peptide_count: int = Field(..., ge=0)
    assay_ready_target_count: int = Field(..., ge=0)
    blocked_target_count: int = Field(..., ge=0)
    retained_assay_count: int = Field(..., ge=0)
    panel_transition_count: int = Field(..., ge=0)


class DiscoveryToAssayArtifactPaths(JsonModel):
    """Stable artifact names exposed by the discovery-to-assay workflow."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = "discovery_to_assay_summary.tsv"
    targets_tsv: str = "discovery_to_assay_targets.tsv"
    selected_peptides_tsv: str = "discovery_to_assay_selected_peptides.tsv"
    rejected_peptides_tsv: str = "discovery_to_assay_rejected_peptides.tsv"
    selected_transitions_tsv: str = "discovery_to_assay_selected_transitions.tsv"
    rejected_transitions_tsv: str = "discovery_to_assay_rejected_transitions.tsv"
    assay_tsv: str = "discovery_to_assay_assays.tsv"
    panel_tsv: str = "discovery_to_assay_panel.tsv"
    omitted_targets_tsv: str = "discovery_to_assay_omitted_targets.tsv"
    validation_candidate_summary_tsv: str = (
        "discovery_to_assay_validation_candidate_summary.tsv"
    )
    validation_candidate_cards_tsv: str = (
        "discovery_to_assay_validation_candidate_cards.tsv"
    )
    validation_candidate_assays_tsv: str = (
        "discovery_to_assay_validation_candidate_assays.tsv"
    )
    validation_candidate_warnings_tsv: str = (
        "discovery_to_assay_validation_candidate_warnings.tsv"
    )


class DiscoveryToAssayManifest(JsonModel):
    """Manifest for the stable discovery-to-assay workflow artifact surface."""

    model_config = ConfigDict(extra="forbid")

    artifacts: DiscoveryToAssayArtifactPaths = Field(
        default_factory=DiscoveryToAssayArtifactPaths
    )


class DiscoveryToAssayReport(WorkflowResult):
    """Workflow-owned discovery-to-assay report with explicit gating surfaces."""

    model_config = ConfigDict(extra="forbid")

    manifest: DiscoveryToAssayManifest = Field(default_factory=DiscoveryToAssayManifest)
    peptide_selection_report: DiscoveryTargetedPeptideSelectionReport
    transition_selection_report: TargetedTransitionSelectionReport
    assay_interference_report: TargetedAssayInterferenceReport
    panel_design_report: TargetedPanelDesignReport
    validation_candidate_cards: ValidationEvidenceCardReport
    target_entries: tuple[DiscoveryAssayTargetEntry, ...] = Field(default_factory=tuple)
    summary: DiscoveryToAssaySummary
    note: str = Field(..., min_length=1)


def design_assay_from_discovery(
    result: DiscoveryAssaySourceResult,
    targets: tuple[DiscoveryAssayTargetInput, ...],
    *,
    top_peptides_per_target: int = 3,
    default_precursor_charge: int = 2,
    fragment_charges: tuple[int, ...] = (1, 2),
    minimum_transition_count: int = 3,
    maximum_transition_count: int = 5,
    minimum_fragment_mz: float = 300.0,
    maximum_fragment_mz: float = 1500.0,
    precursor_exclusion_da: float = 8.0,
    library_match_tolerance_da: float = 0.02,
    missed_cleavages: int = 0,
    precursor_tolerance_da: float = 1.0,
    fragment_tolerance_da: float = 0.02,
    coelution_rt_window_minutes: float = 0.5,
    minimum_export_transitions: int | None = None,
    retention_window_radius_minutes: float = 1.5,
) -> DiscoveryToAssayReport:
    """Design targeted assays from discovery-ranked targets without bypassing peptide gating."""

    peptide_selection_report = build_discovery_targeted_peptide_selection_report(
        _merge_discovery_targets(targets),
        result.peptide_evidence_entries,
        result.protein_records,
        missed_cleavages=missed_cleavages,
        top_peptides_per_target=top_peptides_per_target,
    )
    transition_selection_report = build_targeted_transition_selection_report(
        peptide_selection_report.selected_entries,
        spectral_library_entries=result.spectral_library_entries,
        default_precursor_charge=default_precursor_charge,
        fragment_charges=fragment_charges,
        minimum_transition_count=minimum_transition_count,
        maximum_transition_count=maximum_transition_count,
        minimum_fragment_mz=minimum_fragment_mz,
        maximum_fragment_mz=maximum_fragment_mz,
        precursor_exclusion_da=precursor_exclusion_da,
        library_match_tolerance_da=library_match_tolerance_da,
    )
    assay_interference_report = build_targeted_assay_interference_report(
        peptide_selection_report.selected_entries,
        transition_selection_report.peptide_entries,
        result.protein_records,
        spectral_library_entries=result.spectral_library_entries,
        missed_cleavages=missed_cleavages,
        precursor_tolerance_da=precursor_tolerance_da,
        fragment_tolerance_da=fragment_tolerance_da,
        coelution_rt_window_minutes=coelution_rt_window_minutes,
        minimum_export_transitions=(
            minimum_transition_count
            if minimum_export_transitions is None
            else minimum_export_transitions
        ),
    )
    panel_design_report = build_targeted_panel_design_report(
        biomarker_candidates=_panel_candidates(targets),
        selected_peptides=_panel_selected_peptides(
            peptide_selection_report.selected_entries
        ),
        assay_entries=_panel_assays(assay_interference_report),
        transition_entries=_panel_transitions(assay_interference_report),
        spectral_library_entries=result.spectral_library_entries,
        retention_window_radius_minutes=retention_window_radius_minutes,
    )
    target_entries = _build_target_entries(
        targets=targets,
        peptide_selection_report=peptide_selection_report,
        transition_selection_report=transition_selection_report,
        panel_design_report=panel_design_report,
    )
    validation_candidate_cards = _build_validation_candidate_cards(
        targets=targets,
        target_entries=target_entries,
        panel_design_report=panel_design_report,
    )
    manifest = DiscoveryToAssayManifest()
    summary = DiscoveryToAssaySummary(
        target_count=len(target_entries),
        protein_target_count=sum(
            1
            for entry in target_entries
            if entry.candidate_kind is TargetedPanelCandidateKind.PROTEIN
        ),
        ptm_site_target_count=sum(
            1
            for entry in target_entries
            if entry.candidate_kind is TargetedPanelCandidateKind.PTM_SITE
        ),
        target_with_acceptable_peptide_count=sum(
            1 for entry in target_entries if entry.acceptable_peptide_count > 0
        ),
        assay_ready_target_count=sum(
            1
            for entry in target_entries
            if entry.assay_feasibility is DiscoveryAssayFeasibilityStatus.ASSAY_READY
        ),
        blocked_target_count=sum(
            1
            for entry in target_entries
            if entry.assay_feasibility is not DiscoveryAssayFeasibilityStatus.ASSAY_READY
        ),
        retained_assay_count=len(panel_design_report.assay_entries),
        panel_transition_count=len(panel_design_report.panel_entries),
    )
    return DiscoveryToAssayReport(
        manifest=manifest,
        peptide_selection_report=peptide_selection_report,
        transition_selection_report=transition_selection_report,
        assay_interference_report=assay_interference_report,
        panel_design_report=panel_design_report,
        validation_candidate_cards=validation_candidate_cards,
        target_entries=target_entries,
        artifacts=artifact_name_map(manifest.artifacts),
        warnings=_build_discovery_to_assay_warnings(summary, manifest),
        rejected_evidence=_build_discovery_to_assay_rejected_evidence(
            target_entries,
            manifest,
        ),
        summary=summary,
        note=(
            "discovery-to-assay design composes governed peptide selection, transition "
            "selection, assay interference scoring, panel design, and validation "
            "candidate cards so no target is promoted into an assay without an "
            "acceptable peptide"
        ),
    )


def render_discovery_to_assay_summary_tsv(report: DiscoveryToAssayReport) -> str:
    """Render compact discovery-to-assay workflow accounting as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("target_count", report.summary.target_count))
    writer.writerow(("protein_target_count", report.summary.protein_target_count))
    writer.writerow(("ptm_site_target_count", report.summary.ptm_site_target_count))
    writer.writerow(
        (
            "target_with_acceptable_peptide_count",
            report.summary.target_with_acceptable_peptide_count,
        )
    )
    writer.writerow(("assay_ready_target_count", report.summary.assay_ready_target_count))
    writer.writerow(("blocked_target_count", report.summary.blocked_target_count))
    writer.writerow(("retained_assay_count", report.summary.retained_assay_count))
    writer.writerow(("panel_transition_count", report.summary.panel_transition_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_discovery_to_assay_targets_tsv(report: DiscoveryToAssayReport) -> str:
    """Render target-level discovery-to-assay feasibility rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "site_key",
            "priority_rank",
            "acceptable_peptide_count",
            "transition_supported_peptide_count",
            "retained_assay_count",
            "panel_transition_count",
            "expected_retention_time_available",
            "best_peptide_sequence",
            "best_uniqueness_class",
            "best_liability_tier",
            "liability_codes",
            "assay_feasibility",
            "note",
        )
    )
    for entry in report.target_entries:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                "" if entry.site_key is None else entry.site_key,
                entry.priority_rank,
                entry.acceptable_peptide_count,
                entry.transition_supported_peptide_count,
                entry.retained_assay_count,
                entry.panel_transition_count,
                str(entry.expected_retention_time_available).lower(),
                "" if entry.best_peptide_sequence is None else entry.best_peptide_sequence,
                ""
                if entry.best_uniqueness_class is None
                else entry.best_uniqueness_class.value,
                ""
                if entry.best_liability_tier is None
                else entry.best_liability_tier.value,
                ";".join(entry.liability_codes),
                entry.assay_feasibility.value,
                entry.note,
            )
        )
    return handle.getvalue()


def render_discovery_to_assay_selected_peptides_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render selected peptide rows from the composed workflow report."""

    return cast(
        str,
        render_discovery_targeted_peptide_selection_selected_tsv(
            report.peptide_selection_report
        ),
    )


def render_discovery_to_assay_rejected_peptides_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render rejected peptide rows from the composed workflow report."""

    return cast(
        str,
        render_discovery_targeted_peptide_selection_rejected_tsv(
            report.peptide_selection_report
        ),
    )


def render_discovery_to_assay_selected_transitions_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render selected transition rows from the composed workflow report."""

    return cast(
        str,
        render_targeted_transition_selection_selected_tsv(
            report.transition_selection_report
        ),
    )


def render_discovery_to_assay_rejected_transitions_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render rejected transition rows from the composed workflow report."""

    return cast(
        str,
        render_targeted_transition_selection_rejected_tsv(
            report.transition_selection_report
        ),
    )


def render_discovery_to_assay_assay_tsv(report: DiscoveryToAssayReport) -> str:
    """Render retained assay rows from the composed workflow report."""

    return cast(str, render_targeted_panel_design_assay_tsv(report.panel_design_report))


def render_discovery_to_assay_panel_tsv(report: DiscoveryToAssayReport) -> str:
    """Render retained panel transition rows from the composed workflow report."""

    return cast(str, render_targeted_panel_design_panel_tsv(report.panel_design_report))


def render_discovery_to_assay_omitted_targets_tsv(report: DiscoveryToAssayReport) -> str:
    """Render omitted-target rows from the composed workflow report."""

    return cast(
        str,
        render_targeted_panel_design_omitted_candidate_tsv(report.panel_design_report),
    )


def render_discovery_to_assay_validation_candidate_summary_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render validation-candidate summary rows from the composed workflow report."""

    return cast(
        str,
        render_validation_evidence_card_summary_tsv(report.validation_candidate_cards),
    )


def render_discovery_to_assay_validation_candidate_cards_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render validation-candidate card rows from the composed workflow report."""

    return cast(
        str,
        render_validation_evidence_card_tsv(report.validation_candidate_cards),
    )


def render_discovery_to_assay_validation_candidate_assays_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render validation-candidate assay rows from the composed workflow report."""

    return cast(
        str,
        render_validation_evidence_card_assay_tsv(report.validation_candidate_cards),
    )


def render_discovery_to_assay_validation_candidate_warnings_tsv(
    report: DiscoveryToAssayReport,
) -> str:
    """Render validation-candidate warning rows from the composed workflow report."""

    return cast(
        str,
        render_validation_evidence_card_warning_tsv(report.validation_candidate_cards),
    )


def _build_discovery_to_assay_warnings(
    summary: DiscoveryToAssaySummary,
    manifest: DiscoveryToAssayManifest,
) -> tuple[ResultWarningEntry, ...]:
    warnings: list[ResultWarningEntry] = []
    if summary.blocked_target_count:
        warnings.append(
            build_result_warning(
                warning_id="discovery-to-assay:blocked-targets",
                warning_code="blocked_targets_present",
                source_surface="discovery_to_assay",
                message=(
                    f"{summary.blocked_target_count} discovery-ranked targets remain "
                    "blocked from assay export"
                ),
                related_artifact=manifest.artifacts.omitted_targets_tsv,
            )
        )
    if summary.assay_ready_target_count < summary.target_count:
        warnings.append(
            build_result_warning(
                warning_id="discovery-to-assay:partial-panel-coverage",
                warning_code="partial_assay_coverage",
                source_surface="discovery_to_assay",
                message=(
                    "discovery-ranked targets include peptide-unavailable, "
                    "transition-limited, or site-specific follow-up cases"
                ),
                related_artifact=manifest.artifacts.targets_tsv,
            )
        )
    return tuple(warnings)


def _build_discovery_to_assay_rejected_evidence(
    target_entries: tuple[DiscoveryAssayTargetEntry, ...],
    manifest: DiscoveryToAssayManifest,
) -> tuple[RejectedEvidenceEntry, ...]:
    return tuple(
        build_rejected_evidence_entry(
            evidence_id=f"discovery_to_assay:{entry.candidate_id}",
            source_surface="discovery_to_assay",
            reason_code=_rejected_evidence_reason_code(entry.assay_feasibility),
            message=entry.note,
            related_artifact=manifest.artifacts.omitted_targets_tsv,
            entity_id=entry.candidate_id,
        )
        for entry in target_entries
        if entry.assay_feasibility is not DiscoveryAssayFeasibilityStatus.ASSAY_READY
    )


def _rejected_evidence_reason_code(
    feasibility: DiscoveryAssayFeasibilityStatus,
) -> str:
    if feasibility is DiscoveryAssayFeasibilityStatus.PEPTIDE_UNAVAILABLE:
        return "missing_peptide"
    if feasibility is DiscoveryAssayFeasibilityStatus.SITE_SPECIFIC_FOLLOW_UP_REQUIRED:
        return "review-needs-assay-evidence"
    return "partial_assay_coverage"


def _build_validation_candidate_cards(
    *,
    targets: tuple[DiscoveryAssayTargetInput, ...],
    target_entries: tuple[DiscoveryAssayTargetEntry, ...],
    panel_design_report: TargetedPanelDesignReport,
) -> ValidationEvidenceCardReport:
    target_entry_by_id = {entry.candidate_id: entry for entry in target_entries}
    return build_validation_evidence_card_report(
        tuple(
            ValidationEvidenceDiscoveryInput(
                candidate_id=target.candidate_id,
                candidate_kind=target.candidate_kind,
                display_label=target.display_label,
                target_protein_ref=target.target_protein_ref,
                site_key=target.site_key,
                priority_rank=target.priority_rank,
                final_score=target.final_score,
                weighted_evidence_total=(
                    target.final_score
                    if target.weighted_evidence_total is None
                    else target.weighted_evidence_total
                ),
                penalty_total=target.penalty_total,
                uncertainty=target.uncertainty,
                effect_size=target.effect_size,
                adjusted_p_value=target.adjusted_p_value,
                support_count=target.support_count,
                annotation_labels=target.annotation_labels,
                rank_reason_codes=target.rank_reason_codes,
                source_ids=target.source_ids,
                ranking_note=target.ranking_note,
            )
            for target in targets
        ),
        panel_assays=tuple(
            ValidationEvidencePanelAssayInput(
                assay_entry_id=entry.assay_entry_id,
                biomarker_candidate_id=entry.biomarker_candidate_id,
                biomarker_candidate_kind=entry.biomarker_candidate_kind,
                biomarker_display_label=entry.biomarker_display_label,
                biomarker_priority_rank=entry.biomarker_priority_rank,
                target_protein_ref=entry.target_protein_ref,
                target_protein_group_id=entry.target_protein_group_id,
                gene_symbol=entry.gene_symbol,
                peptide_sequence=entry.peptide_sequence,
                canonical_peptide=entry.canonical_peptide,
                uniqueness_class=entry.uniqueness_class,
                uniqueness_score=entry.uniqueness_score,
                precursor_charge=entry.precursor_charge,
                precursor_mz=entry.precursor_mz,
                expected_retention_time_minutes=entry.expected_retention_time_minutes,
                retention_window_start_minutes=entry.retention_window_start_minutes,
                retention_window_end_minutes=entry.retention_window_end_minutes,
                selected_transition_count=entry.selected_transition_count,
                exported_transition_count=entry.exported_transition_count,
                assay_interference_risk_tier=entry.assay_interference_risk_tier,
                warning_codes=entry.warning_codes,
                warning_note=entry.warning_note,
                source_library_entry_id=entry.source_library_entry_id,
            )
            for entry in panel_design_report.assay_entries
        ),
        omitted_candidates=tuple(
            ValidationEvidenceOmittedCandidateInput(
                candidate_id=entry.candidate_id,
                candidate_kind=entry.candidate_kind,
                display_label=entry.display_label,
                target_protein_ref=entry.target_protein_ref,
                site_key=entry.site_key,
                priority_rank=entry.priority_rank,
                omission_reason=target_entry_by_id.get(entry.candidate_id, entry).note,
            )
            for entry in panel_design_report.omitted_candidates
        ),
    )


def _merge_discovery_targets(
    targets: tuple[DiscoveryAssayTargetInput, ...],
) -> tuple[DiscoveryTargetProteinEntry, ...]:
    merged: dict[tuple[str, str], DiscoveryAssayTargetInput] = {}
    discovery_peptides_by_key: dict[tuple[str, str], list[str]] = {}
    protein_refs_by_key: dict[tuple[str, str], list[str]] = {}
    for target in targets:
        key = (target.target_protein_ref, target.target_protein_group_id)
        merged.setdefault(key, target)
        discovery_peptides_by_key.setdefault(key, []).extend(target.discovery_peptides)
        protein_refs_by_key.setdefault(key, []).extend(
            target.protein_refs or (target.target_protein_ref,)
        )
    return tuple(
        DiscoveryTargetProteinEntry(
            protein_group_id=key[1],
            representative_protein_ref=key[0],
            protein_refs=_ordered_unique(protein_refs_by_key[key]),
            gene_symbol=target.gene_symbol,
            discovery_peptides=_ordered_unique(discovery_peptides_by_key[key]),
        )
        for key, target in sorted(merged.items(), key=lambda item: item[0])
    )


def _panel_candidates(
    targets: tuple[DiscoveryAssayTargetInput, ...],
) -> tuple[TargetedPanelBiomarkerCandidateInput, ...]:
    return tuple(
        TargetedPanelBiomarkerCandidateInput(
            candidate_id=target.candidate_id,
            candidate_kind=target.candidate_kind,
            display_label=target.display_label,
            target_protein_ref=target.target_protein_ref,
            site_key=target.site_key,
            priority_rank=target.priority_rank,
            final_score=target.final_score,
            penalty_total=target.penalty_total,
            rank_reason_codes=target.rank_reason_codes,
        )
        for target in targets
    )


def _panel_selected_peptides(
    selected_entries: tuple[DiscoveryTargetedPeptideSelectionEntry, ...],
) -> tuple[TargetedPanelSelectedPeptideInput, ...]:
    return tuple(
        TargetedPanelSelectedPeptideInput(
            target_protein_ref=entry.target_protein_ref,
            target_protein_group_id=entry.target_protein_group_id,
            gene_symbol=entry.gene_symbol,
            peptide_sequence=entry.peptide_sequence,
            canonical_peptide=entry.canonical_peptide,
            rank=entry.rank,
            observed_in_discovery=entry.observed_in_discovery,
            observed_psm_count=entry.observed_psm_count,
            run_count=entry.run_count,
            detection_frequency=entry.detection_frequency,
            replicate_consistency=entry.replicate_consistency,
            primary_evidence_class=entry.primary_evidence_class,
            uniqueness_class=entry.uniqueness_class,
            uniqueness_score=entry.uniqueness_score,
            detectability_score=entry.detectability_score,
            detectability_tier=entry.detectability_tier,
            suitability_score=entry.suitability_score,
            liability_tier=entry.liability_tier,
            liability_codes=entry.liability_codes,
            selection_score=entry.selection_score,
            selection_reasons=entry.selection_reasons,
        )
        for entry in selected_entries
    )


def _panel_assays(
    interference_report: TargetedAssayInterferenceReport,
) -> tuple[TargetedPanelAssayInput, ...]:
    return tuple(
        TargetedPanelAssayInput(
            assay_entry_id=entry.assay_entry_id,
            target_protein_ref=entry.target_protein_ref,
            target_protein_group_id=entry.target_protein_group_id,
            gene_symbol=entry.gene_symbol,
            peptide_sequence=entry.peptide_sequence,
            canonical_peptide=entry.canonical_peptide,
            peptide_rank=entry.peptide_rank,
            precursor_charge=entry.precursor_charge,
            precursor_mz=entry.precursor_mz,
            selected_transition_count=entry.selected_transition_count,
            exported_transition_count=entry.exported_transition_count,
            interference_risk_score=entry.interference_risk_score,
            interference_risk_tier=entry.interference_risk_tier,
            downgrade_reasons=entry.downgrade_reasons,
            panel_export_allowed=entry.panel_export_allowed,
            panel_export_caveat=entry.panel_export_caveat,
            source_library_entry_id=entry.source_library_entry_id,
        )
        for entry in interference_report.assay_entries
    )


def _panel_transitions(
    interference_report: TargetedAssayInterferenceReport,
) -> tuple[TargetedPanelTransitionInput, ...]:
    return tuple(
        TargetedPanelTransitionInput(
            assay_entry_id=entry.assay_entry_id,
            target_protein_ref=entry.target_protein_ref,
            target_protein_group_id=entry.target_protein_group_id,
            gene_symbol=entry.gene_symbol,
            peptide_sequence=entry.peptide_sequence,
            canonical_peptide=entry.canonical_peptide,
            precursor_charge=entry.precursor_charge,
            precursor_mz=entry.precursor_mz,
            fragment_label=entry.fragment_label,
            ion_type=entry.ion_type.value,
            fragment_ordinal=entry.fragment_ordinal,
            fragment_charge=entry.fragment_charge,
            fragment_sequence=entry.fragment_sequence,
            fragment_mz=entry.fragment_mz,
            expected_relative_intensity=entry.expected_relative_intensity,
            selected_transition_rank=entry.selected_transition_rank,
            interference_risk_score=entry.interference_risk_score,
            interference_risk_tier=entry.interference_risk_tier,
            downgrade_reasons=entry.downgrade_reasons,
            export_allowed=entry.export_allowed,
            export_caveat=entry.export_caveat,
        )
        for entry in interference_report.transition_entries
    )


def _build_target_entries(
    *,
    targets: tuple[DiscoveryAssayTargetInput, ...],
    peptide_selection_report: DiscoveryTargetedPeptideSelectionReport,
    transition_selection_report: TargetedTransitionSelectionReport,
    panel_design_report: TargetedPanelDesignReport,
) -> tuple[DiscoveryAssayTargetEntry, ...]:
    selected_by_protein: dict[str, list[DiscoveryTargetedPeptideSelectionEntry]] = {}
    for entry in peptide_selection_report.selected_entries:
        selected_by_protein.setdefault(entry.target_protein_ref, []).append(entry)
    transitions_by_protein: dict[str, list[TargetedTransitionSelectionPeptideEntry]] = {}
    for entry in transition_selection_report.peptide_entries:
        transitions_by_protein.setdefault(entry.target_protein_ref, []).append(entry)
    assays_by_candidate: dict[str, list[TargetedPanelAssayEntry]] = {}
    for entry in panel_design_report.assay_entries:
        assays_by_candidate.setdefault(entry.biomarker_candidate_id, []).append(entry)
    panel_by_candidate: dict[str, list[TargetedPanelTransitionEntry]] = {}
    for entry in panel_design_report.panel_entries:
        panel_by_candidate.setdefault(entry.biomarker_candidate_id, []).append(entry)

    rows: list[DiscoveryAssayTargetEntry] = []
    for target in sorted(
        targets,
        key=lambda entry: (
            entry.priority_rank,
            entry.target_protein_ref,
            entry.candidate_id,
        ),
    ):
        selected_peptides = tuple(
            sorted(
                selected_by_protein.get(target.target_protein_ref, ()),
                key=lambda entry: (entry.rank, entry.canonical_peptide),
            )
        )
        transition_entries = tuple(
            sorted(
                transitions_by_protein.get(target.target_protein_ref, ()),
                key=lambda entry: (entry.peptide_rank, entry.canonical_peptide),
            )
        )
        retained_assays = tuple(assays_by_candidate.get(target.candidate_id, ()))
        panel_entries = tuple(panel_by_candidate.get(target.candidate_id, ()))
        best_peptide = selected_peptides[0] if selected_peptides else None
        assay_feasibility, note = _assay_feasibility(
            target=target,
            selected_peptide_count=len(selected_peptides),
            transition_supported_peptide_count=sum(
                1 for entry in transition_entries if entry.sufficient_transition_support
            ),
            retained_assay_count=len(retained_assays),
        )
        rows.append(
            DiscoveryAssayTargetEntry(
                candidate_id=target.candidate_id,
                candidate_kind=target.candidate_kind,
                display_label=target.display_label,
                target_protein_ref=target.target_protein_ref,
                target_protein_group_id=target.target_protein_group_id,
                gene_symbol=target.gene_symbol,
                site_key=target.site_key,
                priority_rank=target.priority_rank,
                acceptable_peptide_count=len(selected_peptides),
                transition_supported_peptide_count=sum(
                    1 for entry in transition_entries if entry.sufficient_transition_support
                ),
                retained_assay_count=len(retained_assays),
                panel_transition_count=len(panel_entries),
                expected_retention_time_available=any(
                    entry.source_library_entry_id is not None
                    for entry in transition_entries
                )
                or any(
                    entry.expected_retention_time_minutes is not None
                    for entry in retained_assays
                ),
                best_peptide_sequence=(
                    None if best_peptide is None else best_peptide.canonical_peptide
                ),
                best_uniqueness_class=(
                    None if best_peptide is None else best_peptide.uniqueness_class
                ),
                best_liability_tier=(
                    None if best_peptide is None else best_peptide.liability_tier
                ),
                liability_codes=()
                if best_peptide is None
                else best_peptide.liability_codes,
                assay_feasibility=assay_feasibility,
                note=note,
            )
        )
    return tuple(rows)


def _assay_feasibility(
    *,
    target: DiscoveryAssayTargetInput,
    selected_peptide_count: int,
    transition_supported_peptide_count: int,
    retained_assay_count: int,
) -> tuple[DiscoveryAssayFeasibilityStatus, str]:
    if retained_assay_count > 0:
        return (
            DiscoveryAssayFeasibilityStatus.ASSAY_READY,
            "target is promoted into the final assay panel because at least one acceptable peptide retains enough transitions for export",
        )
    if selected_peptide_count == 0:
        return (
            DiscoveryAssayFeasibilityStatus.PEPTIDE_UNAVAILABLE,
            "no acceptable peptide survived discovery-backed uniqueness and suitability checks for this target",
        )
    if target.candidate_kind is TargetedPanelCandidateKind.PTM_SITE:
        return (
            DiscoveryAssayFeasibilityStatus.SITE_SPECIFIC_FOLLOW_UP_REQUIRED,
            "site target remains visible, but the current workflow only promotes protein-level peptide assays by default",
        )
    if transition_supported_peptide_count == 0:
        return (
            DiscoveryAssayFeasibilityStatus.TRANSITION_LIMITED,
            "acceptable peptide support exists, but retained fragment transitions do not meet the governed export minimum",
        )
    return (
        DiscoveryAssayFeasibilityStatus.TRANSITION_LIMITED,
        "target remains blocked because no retained assay survived the governed interference and export checks",
    )


def _ordered_unique(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return tuple(ordered)


__all__ = [
    "DiscoveryAssayFeasibilityStatus",
    "DiscoveryAssaySourceResult",
    "DiscoveryAssayTargetEntry",
    "DiscoveryAssayTargetInput",
    "DiscoveryToAssayArtifactPaths",
    "DiscoveryToAssayManifest",
    "DiscoveryToAssayReport",
    "DiscoveryToAssaySummary",
    "design_assay_from_discovery",
    "render_discovery_to_assay_assay_tsv",
    "render_discovery_to_assay_omitted_targets_tsv",
    "render_discovery_to_assay_panel_tsv",
    "render_discovery_to_assay_rejected_peptides_tsv",
    "render_discovery_to_assay_rejected_transitions_tsv",
    "render_discovery_to_assay_selected_peptides_tsv",
    "render_discovery_to_assay_selected_transitions_tsv",
    "render_discovery_to_assay_summary_tsv",
    "render_discovery_to_assay_targets_tsv",
    "render_discovery_to_assay_validation_candidate_assays_tsv",
    "render_discovery_to_assay_validation_candidate_cards_tsv",
    "render_discovery_to_assay_validation_candidate_summary_tsv",
    "render_discovery_to_assay_validation_candidate_warnings_tsv",
]
