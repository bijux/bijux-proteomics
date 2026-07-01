# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assemble governed validation evidence cards for biomarker candidates."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.biomarker_stability import BiomarkerStabilityReasonCode
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationReasonCode,
    TargetedValidationVerdict,
)
from bijux_proteomics_foundation import JsonModel


class ValidationEvidenceCardStatus(StrEnum):
    """Stable candidate statuses derived from governed validation evidence."""

    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    READY_FOR_TARGETED_VALIDATION = "ready_for_targeted_validation"
    DEPRIORITIZED_AS_REDUNDANT = "deprioritized_as_redundant"
    BLOCKED_BY_ASSAY_DESIGN = "blocked_by_assay_design"


class ValidationEvidenceWarningCode(StrEnum):
    """Stable warning classes preserved on validation evidence cards."""

    CANDIDATE_PENALIZED = "candidate_penalized"
    ASSAY_DESIGN_OMITTED = "assay_design_omitted"
    ELEVATED_INTERFERENCE_RISK = "elevated_interference_risk"
    NON_UNIQUE_ASSAY = "non_unique_assay"
    STABILITY_DOWNGRADED = "stability_downgraded"
    REDUNDANT_CANDIDATE = "redundant_candidate"
    TARGETED_VALIDATION_CONFLICT = "targeted_validation_conflict"
    TARGETED_SIGNAL_MISSING = "targeted_signal_missing"


class ValidationEvidenceDiscoveryInput(JsonModel):
    """Discovery-side biomarker ranking evidence needed for one candidate card."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    weighted_evidence_total: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    support_count: int = Field(default=0, ge=0)
    annotation_labels: tuple[str, ...] = Field(default_factory=tuple)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class ValidationEvidencePanelAssayInput(JsonModel):
    """Assay-design evidence attached to one biomarker candidate."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    biomarker_candidate_id: str = Field(..., min_length=1)
    biomarker_candidate_kind: TargetedPanelCandidateKind
    biomarker_display_label: str = Field(..., min_length=1)
    biomarker_priority_rank: int = Field(..., ge=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    expected_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_start_minutes: float | None = Field(default=None, ge=0.0)
    retention_window_end_minutes: float | None = Field(default=None, ge=0.0)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(default_factory=tuple)
    warning_note: str = Field(..., min_length=1)
    source_library_entry_id: str | None = None


class ValidationEvidenceOmittedCandidateInput(JsonModel):
    """Panel-design omission preserved beside retained assays."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    omission_reason: str = Field(..., min_length=1)


class ValidationEvidenceResultInput(JsonModel):
    """Candidate-level targeted validation result."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    verdict: TargetedValidationVerdict
    validation_log2_effect: float | None = None
    assay_evidence_count: int = Field(..., ge=0)
    confirmed_assay_count: int = Field(..., ge=0)
    contradicted_assay_count: int = Field(..., ge=0)
    inconclusive_assay_count: int = Field(..., ge=0)
    reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class ValidationEvidenceResultAssayInput(JsonModel):
    """Assay-level targeted validation evidence attached to one candidate card."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    assay_entry_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    uniqueness_class: PeptideUniquenessClass
    validation_log2_effect: float | None = None
    verdict: TargetedValidationVerdict
    reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class ValidationEvidenceStabilityInput(JsonModel):
    """Stability downgrade evidence attached to one candidate card."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    stability_score: float = Field(..., ge=0.0, le=1.0)
    stability_penalty: float = Field(..., ge=0.0)
    downgraded: bool
    instability_reasons: tuple[BiomarkerStabilityReasonCode, ...] = Field(
        default_factory=tuple
    )
    ranking_note: str = Field(..., min_length=1)


class ValidationEvidenceRedundancyInput(JsonModel):
    """Redundancy-reduction evidence attached to one candidate card."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    cluster_id: str = Field(..., min_length=1)
    representative_candidate_id: str = Field(..., min_length=1)
    representative: bool
    dropped: bool
    shared_sample_count: int = Field(..., ge=0)
    max_redundant_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    redundancy_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class ValidationEvidenceCardAssayEntry(JsonModel):
    """One assay-level evidence block nested under one candidate card."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    uniqueness_class: PeptideUniquenessClass
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    panel_warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(
        default_factory=tuple
    )
    targeted_validation_verdict: TargetedValidationVerdict | None = None
    targeted_validation_log2_effect: float | None = None
    targeted_validation_reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class ValidationEvidenceCardWarningEntry(JsonModel):
    """One explicit warning preserved on a validation evidence card."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    warning_code: ValidationEvidenceWarningCode
    note: str = Field(..., min_length=1)


class ValidationEvidenceCardEntry(JsonModel):
    """One governed validation evidence card over one biomarker candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    discovery_priority_rank: int = Field(..., ge=1)
    discovery_final_score: float = Field(..., ge=0.0, le=1.0)
    discovery_weighted_evidence_total: float = Field(..., ge=0.0, le=1.0)
    discovery_penalty_total: float = Field(..., ge=0.0)
    discovery_uncertainty: float = Field(..., ge=0.0, le=1.0)
    discovery_effect_size: float | None = None
    discovery_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    discovery_support_count: int = Field(..., ge=0)
    biological_role_labels: tuple[str, ...] = Field(default_factory=tuple)
    biological_source_ids: tuple[str, ...] = Field(default_factory=tuple)
    discovery_rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    assay_entry_count: int = Field(..., ge=0)
    omitted_reason: str | None = None
    targeted_validation_verdict: TargetedValidationVerdict | None = None
    targeted_validation_log2_effect: float | None = None
    confirmed_assay_count: int = Field(..., ge=0)
    contradicted_assay_count: int = Field(..., ge=0)
    inconclusive_assay_count: int = Field(..., ge=0)
    targeted_validation_reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    stability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    stability_downgraded: bool = False
    stability_reason_codes: tuple[BiomarkerStabilityReasonCode, ...] = Field(
        default_factory=tuple
    )
    redundancy_cluster_id: str | None = None
    representative_candidate_id: str | None = None
    redundancy_representative: bool | None = None
    redundancy_dropped: bool = False
    redundancy_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    final_status: ValidationEvidenceCardStatus
    warning_codes: tuple[ValidationEvidenceWarningCode, ...] = Field(
        default_factory=tuple
    )
    assay_entries: tuple[ValidationEvidenceCardAssayEntry, ...] = Field(
        default_factory=tuple
    )
    warnings: tuple[ValidationEvidenceCardWarningEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class ValidationEvidenceCardSummary(JsonModel):
    """Compact summary over one validation evidence card pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    confirmed_count: int = Field(..., ge=0)
    contradicted_count: int = Field(..., ge=0)
    inconclusive_count: int = Field(..., ge=0)
    ready_for_targeted_validation_count: int = Field(..., ge=0)
    deprioritized_as_redundant_count: int = Field(..., ge=0)
    blocked_by_assay_design_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)


class ValidationEvidenceCardReport(JsonModel):
    """Owned validation evidence cards over discovery, design, and targeted follow-up evidence."""

    model_config = ConfigDict(extra="forbid")

    cards: tuple[ValidationEvidenceCardEntry, ...] = Field(default_factory=tuple)
    summary: ValidationEvidenceCardSummary
    note: str = Field(..., min_length=1)


def build_validation_evidence_card_report(
    discovery_candidates: tuple[ValidationEvidenceDiscoveryInput, ...],
    *,
    panel_assays: tuple[ValidationEvidencePanelAssayInput, ...] = (),
    omitted_candidates: tuple[ValidationEvidenceOmittedCandidateInput, ...] = (),
    targeted_validation_results: tuple[ValidationEvidenceResultInput, ...] = (),
    targeted_validation_assay_evidence: tuple[
        ValidationEvidenceResultAssayInput, ...
    ] = (),
    stability_entries: tuple[ValidationEvidenceStabilityInput, ...] = (),
    redundancy_entries: tuple[ValidationEvidenceRedundancyInput, ...] = (),
) -> ValidationEvidenceCardReport:
    """Build one validation evidence card per biomarker candidate."""

    panel_assays_by_candidate: dict[str, list[ValidationEvidencePanelAssayInput]] = {}
    for assay in panel_assays:
        panel_assays_by_candidate.setdefault(assay.biomarker_candidate_id, []).append(
            assay
        )

    omitted_by_candidate = {entry.candidate_id: entry for entry in omitted_candidates}
    validation_by_candidate = {
        entry.candidate_id: entry for entry in targeted_validation_results
    }
    assay_validation_by_candidate: dict[
        str, list[ValidationEvidenceResultAssayInput]
    ] = {}
    for entry in targeted_validation_assay_evidence:
        assay_validation_by_candidate.setdefault(entry.candidate_id, []).append(entry)
    stability_by_candidate = {entry.candidate_id: entry for entry in stability_entries}
    redundancy_by_candidate = {
        entry.candidate_id: entry for entry in redundancy_entries
    }

    cards: list[ValidationEvidenceCardEntry] = []
    for discovery in sorted(
        discovery_candidates,
        key=lambda item: (item.priority_rank, item.candidate_id),
    ):
        candidate_panel_assays = tuple(
            sorted(
                panel_assays_by_candidate.get(discovery.candidate_id, ()),
                key=lambda item: item.assay_entry_id,
            )
        )
        omitted = omitted_by_candidate.get(discovery.candidate_id)
        validation = validation_by_candidate.get(discovery.candidate_id)
        assay_validations = tuple(
            sorted(
                assay_validation_by_candidate.get(discovery.candidate_id, ()),
                key=lambda item: item.assay_entry_id,
            )
        )
        stability = stability_by_candidate.get(discovery.candidate_id)
        redundancy = redundancy_by_candidate.get(discovery.candidate_id)
        assay_entries = _build_assay_entries(
            panel_assays=candidate_panel_assays,
            assay_validations=assay_validations,
        )
        final_status = _derive_final_status(
            panel_assays=candidate_panel_assays,
            omitted=omitted,
            validation=validation,
            redundancy=redundancy,
        )
        warning_entries = _build_warning_entries(
            discovery=discovery,
            panel_assays=candidate_panel_assays,
            omitted=omitted,
            validation=validation,
            stability=stability,
            redundancy=redundancy,
        )
        cards.append(
            ValidationEvidenceCardEntry(
                candidate_id=discovery.candidate_id,
                candidate_kind=discovery.candidate_kind,
                display_label=discovery.display_label,
                target_protein_ref=discovery.target_protein_ref,
                site_key=discovery.site_key,
                discovery_priority_rank=discovery.priority_rank,
                discovery_final_score=discovery.final_score,
                discovery_weighted_evidence_total=discovery.weighted_evidence_total,
                discovery_penalty_total=discovery.penalty_total,
                discovery_uncertainty=discovery.uncertainty,
                discovery_effect_size=discovery.effect_size,
                discovery_adjusted_p_value=discovery.adjusted_p_value,
                discovery_support_count=discovery.support_count,
                biological_role_labels=discovery.annotation_labels,
                biological_source_ids=discovery.source_ids,
                discovery_rank_reason_codes=discovery.rank_reason_codes,
                assay_entry_count=len(assay_entries),
                omitted_reason=None if omitted is None else omitted.omission_reason,
                targeted_validation_verdict=(
                    None if validation is None else validation.verdict
                ),
                targeted_validation_log2_effect=(
                    None if validation is None else validation.validation_log2_effect
                ),
                confirmed_assay_count=0
                if validation is None
                else validation.confirmed_assay_count,
                contradicted_assay_count=0
                if validation is None
                else validation.contradicted_assay_count,
                inconclusive_assay_count=0
                if validation is None
                else validation.inconclusive_assay_count,
                targeted_validation_reason_codes=(
                    () if validation is None else validation.reason_codes
                ),
                stability_score=None
                if stability is None
                else stability.stability_score,
                stability_downgraded=False
                if stability is None
                else stability.downgraded,
                stability_reason_codes=(
                    () if stability is None else stability.instability_reasons
                ),
                redundancy_cluster_id=(
                    None if redundancy is None else redundancy.cluster_id
                ),
                representative_candidate_id=(
                    None
                    if redundancy is None
                    else redundancy.representative_candidate_id
                ),
                redundancy_representative=(
                    None if redundancy is None else redundancy.representative
                ),
                redundancy_dropped=False if redundancy is None else redundancy.dropped,
                redundancy_reason_codes=(
                    () if redundancy is None else redundancy.redundancy_reason_codes
                ),
                final_status=final_status,
                warning_codes=tuple(entry.warning_code for entry in warning_entries),
                assay_entries=assay_entries,
                warnings=tuple(warning_entries),
                note=_build_card_note(
                    discovery=discovery,
                    final_status=final_status,
                    omitted=omitted,
                    validation=validation,
                    stability=stability,
                    redundancy=redundancy,
                ),
            )
        )

    cards_tuple = tuple(cards)
    return ValidationEvidenceCardReport(
        cards=cards_tuple,
        summary=ValidationEvidenceCardSummary(
            candidate_count=len(cards_tuple),
            confirmed_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status is ValidationEvidenceCardStatus.CONFIRMED
            ),
            contradicted_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status is ValidationEvidenceCardStatus.CONTRADICTED
            ),
            inconclusive_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status is ValidationEvidenceCardStatus.INCONCLUSIVE
            ),
            ready_for_targeted_validation_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status
                is ValidationEvidenceCardStatus.READY_FOR_TARGETED_VALIDATION
            ),
            deprioritized_as_redundant_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status
                is ValidationEvidenceCardStatus.DEPRIORITIZED_AS_REDUNDANT
            ),
            blocked_by_assay_design_count=sum(
                1
                for entry in cards_tuple
                if entry.final_status
                is ValidationEvidenceCardStatus.BLOCKED_BY_ASSAY_DESIGN
            ),
            warning_count=sum(len(entry.warnings) for entry in cards_tuple),
        ),
        note=(
            "validation evidence cards combine discovery ranking, assay design, targeted "
            "validation, stability, redundancy, and biological role evidence into one "
            "candidate-level status object so final states come from governed evidence rather "
            "than manual labels"
        ),
    )


def render_validation_evidence_card_summary_tsv(
    report: ValidationEvidenceCardReport,
) -> str:
    """Render validation evidence card summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(("confirmed_count", report.summary.confirmed_count))
    writer.writerow(("contradicted_count", report.summary.contradicted_count))
    writer.writerow(("inconclusive_count", report.summary.inconclusive_count))
    writer.writerow(
        (
            "ready_for_targeted_validation_count",
            report.summary.ready_for_targeted_validation_count,
        )
    )
    writer.writerow(
        (
            "deprioritized_as_redundant_count",
            report.summary.deprioritized_as_redundant_count,
        )
    )
    writer.writerow(
        ("blocked_by_assay_design_count", report.summary.blocked_by_assay_design_count)
    )
    writer.writerow(("warning_count", report.summary.warning_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_validation_evidence_card_tsv(report: ValidationEvidenceCardReport) -> str:
    """Render flattened validation evidence cards as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "discovery_priority_rank",
            "discovery_final_score",
            "discovery_weighted_evidence_total",
            "discovery_penalty_total",
            "discovery_uncertainty",
            "discovery_effect_size",
            "discovery_adjusted_p_value",
            "discovery_support_count",
            "biological_role_labels",
            "biological_source_ids",
            "discovery_rank_reason_codes",
            "assay_entry_count",
            "omitted_reason",
            "targeted_validation_verdict",
            "targeted_validation_log2_effect",
            "confirmed_assay_count",
            "contradicted_assay_count",
            "inconclusive_assay_count",
            "targeted_validation_reason_codes",
            "stability_score",
            "stability_downgraded",
            "stability_reason_codes",
            "redundancy_cluster_id",
            "representative_candidate_id",
            "redundancy_representative",
            "redundancy_dropped",
            "redundancy_reason_codes",
            "final_status",
            "warning_codes",
            "note",
        )
    )
    for entry in report.cards:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.discovery_priority_rank,
                _format_float(entry.discovery_final_score),
                _format_float(entry.discovery_weighted_evidence_total),
                _format_float(entry.discovery_penalty_total),
                _format_float(entry.discovery_uncertainty),
                _format_float(entry.discovery_effect_size),
                _format_float(entry.discovery_adjusted_p_value),
                entry.discovery_support_count,
                ";".join(entry.biological_role_labels),
                ";".join(entry.biological_source_ids),
                ";".join(entry.discovery_rank_reason_codes),
                entry.assay_entry_count,
                "" if entry.omitted_reason is None else entry.omitted_reason,
                ""
                if entry.targeted_validation_verdict is None
                else entry.targeted_validation_verdict.value,
                _format_float(entry.targeted_validation_log2_effect),
                entry.confirmed_assay_count,
                entry.contradicted_assay_count,
                entry.inconclusive_assay_count,
                ";".join(
                    reason.value for reason in entry.targeted_validation_reason_codes
                ),
                _format_float(entry.stability_score),
                str(entry.stability_downgraded).lower(),
                ";".join(reason.value for reason in entry.stability_reason_codes),
                ""
                if entry.redundancy_cluster_id is None
                else entry.redundancy_cluster_id,
                ""
                if entry.representative_candidate_id is None
                else entry.representative_candidate_id,
                (
                    ""
                    if entry.redundancy_representative is None
                    else str(entry.redundancy_representative).lower()
                ),
                str(entry.redundancy_dropped).lower(),
                ";".join(entry.redundancy_reason_codes),
                entry.final_status.value,
                ";".join(code.value for code in entry.warning_codes),
                entry.note,
            )
        )
    return handle.getvalue()


def render_validation_evidence_card_assay_tsv(
    report: ValidationEvidenceCardReport,
) -> str:
    """Render assay-level evidence nested under validation cards as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "final_status",
            "assay_entry_id",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "uniqueness_class",
            "assay_interference_risk_tier",
            "panel_warning_codes",
            "targeted_validation_verdict",
            "targeted_validation_log2_effect",
            "targeted_validation_reason_codes",
            "note",
        )
    )
    for card in report.cards:
        for assay in card.assay_entries:
            writer.writerow(
                (
                    card.candidate_id,
                    card.final_status.value,
                    assay.assay_entry_id,
                    assay.peptide_sequence,
                    assay.canonical_peptide,
                    assay.precursor_charge,
                    assay.uniqueness_class.value,
                    assay.assay_interference_risk_tier.value,
                    ";".join(code.value for code in assay.panel_warning_codes),
                    ""
                    if assay.targeted_validation_verdict is None
                    else assay.targeted_validation_verdict.value,
                    _format_float(assay.targeted_validation_log2_effect),
                    ";".join(
                        reason.value
                        for reason in assay.targeted_validation_reason_codes
                    ),
                    assay.note,
                )
            )
    return handle.getvalue()


def render_validation_evidence_card_warning_tsv(
    report: ValidationEvidenceCardReport,
) -> str:
    """Render one explicit warning row per candidate warning."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("candidate_id", "warning_code", "note"))
    for card in report.cards:
        for warning in card.warnings:
            writer.writerow(
                (warning.candidate_id, warning.warning_code.value, warning.note)
            )
    return handle.getvalue()


def _build_assay_entries(
    *,
    panel_assays: tuple[ValidationEvidencePanelAssayInput, ...],
    assay_validations: tuple[ValidationEvidenceResultAssayInput, ...],
) -> tuple[ValidationEvidenceCardAssayEntry, ...]:
    validation_by_assay = {entry.assay_entry_id: entry for entry in assay_validations}
    entries: list[ValidationEvidenceCardAssayEntry] = []
    for assay in panel_assays:
        validation = validation_by_assay.get(assay.assay_entry_id)
        entries.append(
            ValidationEvidenceCardAssayEntry(
                assay_entry_id=assay.assay_entry_id,
                peptide_sequence=assay.peptide_sequence,
                canonical_peptide=assay.canonical_peptide,
                precursor_charge=assay.precursor_charge,
                uniqueness_class=assay.uniqueness_class,
                assay_interference_risk_tier=assay.assay_interference_risk_tier,
                panel_warning_codes=assay.warning_codes,
                targeted_validation_verdict=(
                    None if validation is None else validation.verdict
                ),
                targeted_validation_log2_effect=(
                    None if validation is None else validation.validation_log2_effect
                ),
                targeted_validation_reason_codes=(
                    () if validation is None else validation.reason_codes
                ),
                note=(assay.warning_note if validation is None else validation.note),
            )
        )
    return tuple(entries)


def _derive_final_status(
    *,
    panel_assays: tuple[ValidationEvidencePanelAssayInput, ...],
    omitted: ValidationEvidenceOmittedCandidateInput | None,
    validation: ValidationEvidenceResultInput | None,
    redundancy: ValidationEvidenceRedundancyInput | None,
) -> ValidationEvidenceCardStatus:
    if validation is not None:
        if validation.verdict is TargetedValidationVerdict.CONFIRMED:
            return ValidationEvidenceCardStatus.CONFIRMED
        if validation.verdict is TargetedValidationVerdict.CONTRADICTED:
            return ValidationEvidenceCardStatus.CONTRADICTED
        return ValidationEvidenceCardStatus.INCONCLUSIVE
    if redundancy is not None and redundancy.dropped:
        return ValidationEvidenceCardStatus.DEPRIORITIZED_AS_REDUNDANT
    if not panel_assays:
        return ValidationEvidenceCardStatus.BLOCKED_BY_ASSAY_DESIGN
    if omitted is not None and not panel_assays:
        return ValidationEvidenceCardStatus.BLOCKED_BY_ASSAY_DESIGN
    return ValidationEvidenceCardStatus.READY_FOR_TARGETED_VALIDATION


def _build_warning_entries(
    *,
    discovery: ValidationEvidenceDiscoveryInput,
    panel_assays: tuple[ValidationEvidencePanelAssayInput, ...],
    omitted: ValidationEvidenceOmittedCandidateInput | None,
    validation: ValidationEvidenceResultInput | None,
    stability: ValidationEvidenceStabilityInput | None,
    redundancy: ValidationEvidenceRedundancyInput | None,
) -> list[ValidationEvidenceCardWarningEntry]:
    entries: list[ValidationEvidenceCardWarningEntry] = []
    if discovery.penalty_total > 0.0:
        entries.append(
            ValidationEvidenceCardWarningEntry(
                candidate_id=discovery.candidate_id,
                warning_code=ValidationEvidenceWarningCode.CANDIDATE_PENALIZED,
                note=discovery.ranking_note,
            )
        )
    if omitted is not None:
        entries.append(
            ValidationEvidenceCardWarningEntry(
                candidate_id=discovery.candidate_id,
                warning_code=ValidationEvidenceWarningCode.ASSAY_DESIGN_OMITTED,
                note=omitted.omission_reason,
            )
        )
    if stability is not None and stability.downgraded:
        entries.append(
            ValidationEvidenceCardWarningEntry(
                candidate_id=discovery.candidate_id,
                warning_code=ValidationEvidenceWarningCode.STABILITY_DOWNGRADED,
                note=stability.ranking_note,
            )
        )
    if redundancy is not None and redundancy.dropped:
        entries.append(
            ValidationEvidenceCardWarningEntry(
                candidate_id=discovery.candidate_id,
                warning_code=ValidationEvidenceWarningCode.REDUNDANT_CANDIDATE,
                note=redundancy.ranking_note,
            )
        )
    for assay in panel_assays:
        if (
            assay.assay_interference_risk_tier
            is not TargetedAssayInterferenceRiskTier.LOW
        ):
            entries.append(
                ValidationEvidenceCardWarningEntry(
                    candidate_id=discovery.candidate_id,
                    warning_code=ValidationEvidenceWarningCode.ELEVATED_INTERFERENCE_RISK,
                    note=assay.warning_note,
                )
            )
        if assay.uniqueness_class is not PeptideUniquenessClass.UNIQUE:
            entries.append(
                ValidationEvidenceCardWarningEntry(
                    candidate_id=discovery.candidate_id,
                    warning_code=ValidationEvidenceWarningCode.NON_UNIQUE_ASSAY,
                    note=assay.warning_note,
                )
            )
    if validation is not None:
        if (
            TargetedValidationReasonCode.CONFLICTING_VALIDATION_ASSAYS
            in validation.reason_codes
        ):
            entries.append(
                ValidationEvidenceCardWarningEntry(
                    candidate_id=discovery.candidate_id,
                    warning_code=ValidationEvidenceWarningCode.TARGETED_VALIDATION_CONFLICT,
                    note=validation.note,
                )
            )
        if {
            TargetedValidationReasonCode.VALIDATION_SIGNAL_MISSING,
            TargetedValidationReasonCode.NO_MATCHING_TARGETED_SIGNAL,
        }.intersection(validation.reason_codes):
            entries.append(
                ValidationEvidenceCardWarningEntry(
                    candidate_id=discovery.candidate_id,
                    warning_code=ValidationEvidenceWarningCode.TARGETED_SIGNAL_MISSING,
                    note=validation.note,
                )
            )
    deduped: dict[
        tuple[ValidationEvidenceWarningCode, str], ValidationEvidenceCardWarningEntry
    ] = {}
    for entry in entries:
        deduped[(entry.warning_code, entry.note)] = entry
    return list(deduped.values())


def _build_card_note(
    *,
    discovery: ValidationEvidenceDiscoveryInput,
    final_status: ValidationEvidenceCardStatus,
    omitted: ValidationEvidenceOmittedCandidateInput | None,
    validation: ValidationEvidenceResultInput | None,
    stability: ValidationEvidenceStabilityInput | None,
    redundancy: ValidationEvidenceRedundancyInput | None,
) -> str:
    if (
        final_status is ValidationEvidenceCardStatus.CONFIRMED
        and validation is not None
    ):
        return (
            f"{discovery.candidate_id} is confirmed by targeted validation after discovery ranked "
            f"it at priority {discovery.priority_rank}"
        )
    if (
        final_status is ValidationEvidenceCardStatus.CONTRADICTED
        and validation is not None
    ):
        return (
            f"{discovery.candidate_id} is contradicted by targeted validation despite discovery "
            "support and should not keep a positive validation label"
        )
    if (
        final_status is ValidationEvidenceCardStatus.INCONCLUSIVE
        and validation is not None
    ):
        return (
            f"{discovery.candidate_id} remains inconclusive because targeted validation does not "
            "yet resolve the discovery claim cleanly"
        )
    if (
        final_status is ValidationEvidenceCardStatus.DEPRIORITIZED_AS_REDUNDANT
        and redundancy is not None
    ):
        return (
            f"{discovery.candidate_id} is deprioritized because redundancy analysis keeps "
            f"{redundancy.representative_candidate_id} as the explicit representative"
        )
    if (
        final_status is ValidationEvidenceCardStatus.BLOCKED_BY_ASSAY_DESIGN
        and omitted is not None
    ):
        return f"{discovery.candidate_id} is blocked by assay design because {omitted.omission_reason}"
    if stability is not None and stability.downgraded:
        return (
            f"{discovery.candidate_id} remains available for targeted follow-up but carries "
            "stability-driven warnings that should shape the final validation plan"
        )
    return (
        f"{discovery.candidate_id} is ready for targeted validation with discovery evidence, "
        "biological role context, and governed assay design support"
    )


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"
