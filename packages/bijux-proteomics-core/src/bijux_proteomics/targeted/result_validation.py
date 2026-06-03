# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validate targeted PRM/SRM results against discovery biomarker claims."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
import math
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.errors import DesignError, ScientificEvidenceError
from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.assay_qc import (
    TargetedTargetQcEntry,
    build_targeted_assay_qc_report,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics_foundation import JsonModel


class TargetedValidationDirection(StrEnum):
    """Stable directional labels for discovery and targeted comparisons."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    UNKNOWN = "unknown"


class TargetedValidationVerdict(StrEnum):
    """Stable targeted validation verdicts over discovery candidates."""

    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


class TargetedValidationReasonCode(StrEnum):
    """Stable reasons behind targeted validation outcomes."""

    VALIDATION_EFFECT_MATCHES_DISCOVERY = "validation_effect_matches_discovery"
    VALIDATION_EFFECT_OPPOSES_DISCOVERY = "validation_effect_opposes_discovery"
    VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY = (
        "validation_effect_flat_against_discovery"
    )
    WEAK_VALIDATION_EFFECT = "weak_validation_effect"
    INSUFFICIENT_RELIABLE_REPLICATES = "insufficient_reliable_replicates"
    VALIDATION_SIGNAL_MISSING = "validation_signal_missing"
    NON_UNIQUE_VALIDATION_ASSAY = "non_unique_validation_assay"
    AMBIGUOUS_TARGETED_RESULT_MAPPING = "ambiguous_targeted_result_mapping"
    NO_MATCHING_TARGETED_SIGNAL = "no_matching_targeted_signal"
    DISCOVERY_DIRECTION_MISSING = "discovery_direction_missing"
    NOT_ASSAYED_IN_VALIDATION_PANEL = "not_assayed_in_validation_panel"
    SITE_SPECIFIC_VALIDATION_NOT_AVAILABLE = "site_specific_validation_not_available"
    CONFLICTING_VALIDATION_ASSAYS = "conflicting_validation_assays"


class TargetedResultValidationPolicy(JsonModel):
    """Explicit comparison policy for targeted validation against discovery claims."""

    model_config = ConfigDict(extra="forbid")

    case_condition: str = Field(..., min_length=1)
    control_condition: str = Field(..., min_length=1)
    minimum_reliable_replicates_per_condition: int = Field(default=2, ge=1)
    minimum_absolute_validation_log2_effect: float = Field(default=0.4, ge=0.0)
    flat_validation_log2_threshold: float = Field(default=0.2, ge=0.0)


class TargetedValidationDiscoveryClaimInput(JsonModel):
    """Minimal discovery claim context required for targeted comparison."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    discovery_effect_size: float | None = None
    support_count: int = Field(default=0, ge=0)
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    assay_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class TargetedValidationPanelAssayInput(JsonModel):
    """Minimal targeted assay context required for discovery validation."""

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
    precursor_charge: int = Field(..., ge=1)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(default_factory=tuple)
    warning_note: str = Field(..., min_length=1)


class TargetedValidationAssayEvidenceEntry(JsonModel):
    """One assay-resolved targeted comparison against a discovery claim."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    uniqueness_class: PeptideUniquenessClass
    matched_target_id: str | None = None
    matched_target_count: int = Field(..., ge=0)
    case_condition: str = Field(..., min_length=1)
    control_condition: str = Field(..., min_length=1)
    case_reliable_sample_count: int = Field(..., ge=0)
    control_reliable_sample_count: int = Field(..., ge=0)
    case_mean_log2_intensity: float | None = None
    control_mean_log2_intensity: float | None = None
    validation_log2_effect: float | None = None
    discovery_effect_size: float | None = None
    discovery_direction: TargetedValidationDirection
    validation_direction: TargetedValidationDirection
    verdict: TargetedValidationVerdict
    reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class TargetedValidationEntry(JsonModel):
    """One candidate-level targeted validation verdict against discovery evidence."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    discovery_effect_size: float | None = None
    discovery_direction: TargetedValidationDirection
    validation_log2_effect: float | None = None
    validation_direction: TargetedValidationDirection
    verdict: TargetedValidationVerdict
    assay_evidence_count: int = Field(..., ge=0)
    confirmed_assay_count: int = Field(..., ge=0)
    contradicted_assay_count: int = Field(..., ge=0)
    inconclusive_assay_count: int = Field(..., ge=0)
    reason_codes: tuple[TargetedValidationReasonCode, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class TargetedResultValidationSummary(JsonModel):
    """Compact summary over one targeted validation pass."""

    model_config = ConfigDict(extra="forbid")

    discovery_claim_count: int = Field(..., ge=0)
    assayed_candidate_count: int = Field(..., ge=0)
    confirmed_count: int = Field(..., ge=0)
    contradicted_count: int = Field(..., ge=0)
    inconclusive_count: int = Field(..., ge=0)
    assay_evidence_count: int = Field(..., ge=0)
    unassayed_candidate_count: int = Field(..., ge=0)
    conflicting_candidate_count: int = Field(..., ge=0)


class TargetedResultValidationReport(JsonModel):
    """Owned targeted result validation over discovery biomarker claims."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    policy: TargetedResultValidationPolicy
    assay_qc_summary: dict[str, object] = Field(default_factory=dict)
    entries: tuple[TargetedValidationEntry, ...] = Field(default_factory=tuple)
    assay_evidence: tuple[TargetedValidationAssayEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetedResultValidationSummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _ImportedTargetDescriptor:
    target_id: str
    peptide_sequence: str
    precursor_charge: int | None
    protein_refs: tuple[str, ...]


def build_targeted_result_validation_report(
    discovery_claims: tuple[TargetedValidationDiscoveryClaimInput, ...],
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...],
    import_report: TargetedResultImportReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: TargetedResultValidationPolicy,
) -> TargetedResultValidationReport:
    """Compare targeted PRM/SRM results back to discovery biomarker claims."""

    assay_qc_report = build_targeted_assay_qc_report(import_report, design_entries)
    sample_ids = {item.sample_id for item in import_report.observations}
    condition_by_sample = {
        entry.sample_id: entry.condition
        for entry in design_entries
        if entry.sample_id in sample_ids
    }
    if policy.case_condition == policy.control_condition:
        raise DesignError("case_condition and control_condition must differ")
    if policy.case_condition not in condition_by_sample.values():
        raise DesignError(
            f"case_condition {policy.case_condition!r} is not present in targeted design entries"
        )
    if policy.control_condition not in condition_by_sample.values():
        raise DesignError(
            f"control_condition {policy.control_condition!r} is not present in targeted design entries"
        )

    descriptors = _build_imported_target_descriptors(import_report)
    target_qc_by_target_sample = {
        (entry.target_id, entry.sample_id): entry for entry in assay_qc_report.target_qc
    }
    assays_by_candidate_id: dict[str, list[TargetedValidationPanelAssayInput]] = {}
    for assay in panel_assays:
        assays_by_candidate_id.setdefault(assay.biomarker_candidate_id, []).append(
            assay
        )

    assay_evidence: list[TargetedValidationAssayEvidenceEntry] = []
    candidate_entries: list[TargetedValidationEntry] = []
    for claim in sorted(
        discovery_claims, key=lambda item: (item.priority_rank, item.candidate_id)
    ):
        claim_assays = sorted(
            assays_by_candidate_id.get(claim.candidate_id, ()),
            key=lambda item: (item.biomarker_priority_rank, item.assay_entry_id),
        )
        candidate_assay_evidence = tuple(
            _build_assay_evidence_entry(
                claim=claim,
                assay=assay,
                descriptors=descriptors,
                target_qc_by_target_sample=target_qc_by_target_sample,
                condition_by_sample=condition_by_sample,
                policy=policy,
            )
            for assay in claim_assays
        )
        assay_evidence.extend(candidate_assay_evidence)
        candidate_entries.append(
            _build_candidate_validation_entry(
                claim=claim,
                assay_evidence=candidate_assay_evidence,
            )
        )

    candidate_entries.sort(
        key=lambda item: (
            item.priority_rank,
            item.target_protein_ref,
            item.candidate_id,
        )
    )
    assay_evidence.sort(
        key=lambda item: (
            next(
                entry.priority_rank
                for entry in candidate_entries
                if entry.candidate_id == item.candidate_id
            ),
            item.candidate_id,
            item.assay_entry_id,
        )
    )

    entries_tuple = tuple(candidate_entries)
    assay_evidence_tuple = tuple(assay_evidence)
    return TargetedResultValidationReport(
        source_name=import_report.source_name,
        policy=policy,
        assay_qc_summary=assay_qc_report.summary.to_dict(),
        entries=entries_tuple,
        assay_evidence=assay_evidence_tuple,
        summary=TargetedResultValidationSummary(
            discovery_claim_count=len(discovery_claims),
            assayed_candidate_count=sum(
                1 for entry in entries_tuple if entry.assay_evidence_count > 0
            ),
            confirmed_count=sum(
                1
                for entry in entries_tuple
                if entry.verdict is TargetedValidationVerdict.CONFIRMED
            ),
            contradicted_count=sum(
                1
                for entry in entries_tuple
                if entry.verdict is TargetedValidationVerdict.CONTRADICTED
            ),
            inconclusive_count=sum(
                1
                for entry in entries_tuple
                if entry.verdict is TargetedValidationVerdict.INCONCLUSIVE
            ),
            assay_evidence_count=len(assay_evidence_tuple),
            unassayed_candidate_count=sum(
                1
                for entry in entries_tuple
                if TargetedValidationReasonCode.NOT_ASSAYED_IN_VALIDATION_PANEL
                in entry.reason_codes
                or TargetedValidationReasonCode.SITE_SPECIFIC_VALIDATION_NOT_AVAILABLE
                in entry.reason_codes
            ),
            conflicting_candidate_count=sum(
                1
                for entry in entries_tuple
                if TargetedValidationReasonCode.CONFLICTING_VALIDATION_ASSAYS
                in entry.reason_codes
            ),
        ),
        note=(
            "targeted validation compares discovery biomarker claims back to assay-backed PRM/SRM evidence under explicit case and control conditions so confirmation, contradiction, and technical inconclusiveness remain separate"
        ),
    )


def render_targeted_result_validation_summary_tsv(
    report: TargetedResultValidationReport,
) -> str:
    """Render targeted result validation summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("source_name", report.source_name))
    writer.writerow(("case_condition", report.policy.case_condition))
    writer.writerow(("control_condition", report.policy.control_condition))
    writer.writerow(("discovery_claim_count", report.summary.discovery_claim_count))
    writer.writerow(("assayed_candidate_count", report.summary.assayed_candidate_count))
    writer.writerow(("confirmed_count", report.summary.confirmed_count))
    writer.writerow(("contradicted_count", report.summary.contradicted_count))
    writer.writerow(("inconclusive_count", report.summary.inconclusive_count))
    writer.writerow(("assay_evidence_count", report.summary.assay_evidence_count))
    writer.writerow(
        ("unassayed_candidate_count", report.summary.unassayed_candidate_count)
    )
    writer.writerow(
        ("conflicting_candidate_count", report.summary.conflicting_candidate_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_targeted_result_validation_tsv(
    report: TargetedResultValidationReport,
    verdict: TargetedValidationVerdict,
) -> str:
    """Render candidate-level targeted validation rows for one verdict."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "discovery_effect_size",
            "discovery_direction",
            "validation_log2_effect",
            "validation_direction",
            "verdict",
            "assay_evidence_count",
            "confirmed_assay_count",
            "contradicted_assay_count",
            "inconclusive_assay_count",
            "reason_codes",
            "note",
        )
    )
    for entry in report.entries:
        if entry.verdict is not verdict:
            continue
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.priority_rank,
                ""
                if entry.discovery_effect_size is None
                else f"{entry.discovery_effect_size:g}",
                entry.discovery_direction.value,
                ""
                if entry.validation_log2_effect is None
                else f"{entry.validation_log2_effect:g}",
                entry.validation_direction.value,
                entry.verdict.value,
                entry.assay_evidence_count,
                entry.confirmed_assay_count,
                entry.contradicted_assay_count,
                entry.inconclusive_assay_count,
                ";".join(reason.value for reason in entry.reason_codes),
                entry.note,
            )
        )
    return handle.getvalue()


def render_targeted_result_validation_evidence_tsv(
    report: TargetedResultValidationReport,
) -> str:
    """Render assay-resolved targeted validation evidence as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "assay_entry_id",
            "target_protein_ref",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "uniqueness_class",
            "matched_target_id",
            "matched_target_count",
            "case_condition",
            "control_condition",
            "case_reliable_sample_count",
            "control_reliable_sample_count",
            "case_mean_log2_intensity",
            "control_mean_log2_intensity",
            "validation_log2_effect",
            "discovery_effect_size",
            "discovery_direction",
            "validation_direction",
            "verdict",
            "reason_codes",
            "note",
        )
    )
    for entry in report.assay_evidence:
        writer.writerow(
            (
                entry.candidate_id,
                entry.assay_entry_id,
                entry.target_protein_ref,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.precursor_charge,
                entry.uniqueness_class.value,
                "" if entry.matched_target_id is None else entry.matched_target_id,
                entry.matched_target_count,
                entry.case_condition,
                entry.control_condition,
                entry.case_reliable_sample_count,
                entry.control_reliable_sample_count,
                ""
                if entry.case_mean_log2_intensity is None
                else f"{entry.case_mean_log2_intensity:g}",
                ""
                if entry.control_mean_log2_intensity is None
                else f"{entry.control_mean_log2_intensity:g}",
                ""
                if entry.validation_log2_effect is None
                else f"{entry.validation_log2_effect:g}",
                ""
                if entry.discovery_effect_size is None
                else f"{entry.discovery_effect_size:g}",
                entry.discovery_direction.value,
                entry.validation_direction.value,
                entry.verdict.value,
                ";".join(reason.value for reason in entry.reason_codes),
                entry.note,
            )
        )
    return handle.getvalue()


def _build_imported_target_descriptors(
    import_report: TargetedResultImportReport,
) -> dict[str, _ImportedTargetDescriptor]:
    grouped: dict[str, list[tuple[str, int | None, str | None]]] = {}
    for observation in import_report.observations:
        grouped.setdefault(observation.precursor_id, []).append(
            (
                observation.peptide_sequence,
                observation.precursor_charge,
                observation.protein_ref,
            )
        )
    descriptors: dict[str, _ImportedTargetDescriptor] = {}
    for target_id, values in grouped.items():
        peptide_sequence = values[0][0]
        precursor_charge = next(
            (charge for _, charge, _ in values if charge is not None),
            values[0][1],
        )
        protein_refs = tuple(
            sorted({protein for _, _, protein in values if protein is not None})
        )
        descriptors[target_id] = _ImportedTargetDescriptor(
            target_id=target_id,
            peptide_sequence=peptide_sequence,
            precursor_charge=precursor_charge,
            protein_refs=protein_refs,
        )
    return descriptors


def _build_assay_evidence_entry(
    *,
    claim: TargetedValidationDiscoveryClaimInput,
    assay: TargetedValidationPanelAssayInput,
    descriptors: dict[str, _ImportedTargetDescriptor],
    target_qc_by_target_sample: dict[tuple[str, str], TargetedTargetQcEntry],
    condition_by_sample: dict[str, str],
    policy: TargetedResultValidationPolicy,
) -> TargetedValidationAssayEvidenceEntry:
    matched_target_ids = _match_assay_target_ids(assay, descriptors)
    discovery_direction = _direction_from_effect(
        claim.discovery_effect_size,
        flat_threshold=policy.flat_validation_log2_threshold,
    )
    reasons: list[TargetedValidationReasonCode] = []
    validation_direction = TargetedValidationDirection.UNKNOWN
    case_mean_log2_intensity: float | None = None
    control_mean_log2_intensity: float | None = None
    validation_log2_effect: float | None = None
    case_reliable_sample_count = 0
    control_reliable_sample_count = 0
    matched_target_id: str | None = None

    if assay.uniqueness_class is not PeptideUniquenessClass.UNIQUE:
        reasons.append(TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY)
    if not matched_target_ids:
        reasons.append(TargetedValidationReasonCode.NO_MATCHING_TARGETED_SIGNAL)
    elif len(matched_target_ids) > 1:
        reasons.append(TargetedValidationReasonCode.AMBIGUOUS_TARGETED_RESULT_MAPPING)
    else:
        matched_target_id = matched_target_ids[0]
        case_values, control_values = _collect_condition_log2_intensities(
            matched_target_id=matched_target_id,
            target_qc_by_target_sample=target_qc_by_target_sample,
            condition_by_sample=condition_by_sample,
            policy=policy,
        )
        case_reliable_sample_count = len(case_values)
        control_reliable_sample_count = len(control_values)
        if case_values:
            case_mean_log2_intensity = sum(case_values) / len(case_values)
        if control_values:
            control_mean_log2_intensity = sum(control_values) / len(control_values)
        if (
            case_reliable_sample_count
            < policy.minimum_reliable_replicates_per_condition
            or control_reliable_sample_count
            < policy.minimum_reliable_replicates_per_condition
        ):
            reasons.append(
                TargetedValidationReasonCode.INSUFFICIENT_RELIABLE_REPLICATES
            )
            if case_reliable_sample_count == 0 or control_reliable_sample_count == 0:
                reasons.append(TargetedValidationReasonCode.VALIDATION_SIGNAL_MISSING)
        else:
            if case_mean_log2_intensity is None or control_mean_log2_intensity is None:
                raise ScientificEvidenceError(
                    "targeted validation requires condition means when reliable replicate thresholds are satisfied"
                )
            validation_log2_effect = (
                case_mean_log2_intensity - control_mean_log2_intensity
            )
            validation_direction = _direction_from_effect(
                validation_log2_effect,
                flat_threshold=policy.flat_validation_log2_threshold,
            )
            blocking_reasons = {
                TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY,
                TargetedValidationReasonCode.AMBIGUOUS_TARGETED_RESULT_MAPPING,
                TargetedValidationReasonCode.NO_MATCHING_TARGETED_SIGNAL,
                TargetedValidationReasonCode.INSUFFICIENT_RELIABLE_REPLICATES,
                TargetedValidationReasonCode.VALIDATION_SIGNAL_MISSING,
            }
            if set(reasons).intersection(blocking_reasons):
                pass
            elif discovery_direction is TargetedValidationDirection.UNKNOWN:
                reasons.append(TargetedValidationReasonCode.DISCOVERY_DIRECTION_MISSING)
            elif (
                abs(validation_log2_effect)
                < policy.minimum_absolute_validation_log2_effect
            ):
                if (
                    claim.discovery_effect_size is not None
                    and abs(claim.discovery_effect_size)
                    >= policy.minimum_absolute_validation_log2_effect
                ):
                    reasons.append(
                        TargetedValidationReasonCode.VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY
                    )
                else:
                    reasons.append(TargetedValidationReasonCode.WEAK_VALIDATION_EFFECT)
            elif validation_direction is discovery_direction:
                reasons.append(
                    TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY
                )
            else:
                reasons.append(
                    TargetedValidationReasonCode.VALIDATION_EFFECT_OPPOSES_DISCOVERY
                )

    verdict = _evidence_verdict_from_reasons(reasons)
    return TargetedValidationAssayEvidenceEntry(
        candidate_id=claim.candidate_id,
        assay_entry_id=assay.assay_entry_id,
        target_protein_ref=assay.target_protein_ref,
        peptide_sequence=assay.peptide_sequence,
        canonical_peptide=assay.canonical_peptide,
        precursor_charge=assay.precursor_charge,
        uniqueness_class=assay.uniqueness_class,
        matched_target_id=matched_target_id,
        matched_target_count=len(matched_target_ids),
        case_condition=policy.case_condition,
        control_condition=policy.control_condition,
        case_reliable_sample_count=case_reliable_sample_count,
        control_reliable_sample_count=control_reliable_sample_count,
        case_mean_log2_intensity=case_mean_log2_intensity,
        control_mean_log2_intensity=control_mean_log2_intensity,
        validation_log2_effect=validation_log2_effect,
        discovery_effect_size=claim.discovery_effect_size,
        discovery_direction=discovery_direction,
        validation_direction=validation_direction,
        verdict=verdict,
        reason_codes=_sorted_reason_codes(reasons),
        note=_build_assay_note(
            verdict=verdict,
            assay=assay,
            reasons=reasons,
            policy=policy,
            case_reliable_sample_count=case_reliable_sample_count,
            control_reliable_sample_count=control_reliable_sample_count,
            validation_log2_effect=validation_log2_effect,
        ),
    )


def _build_candidate_validation_entry(
    *,
    claim: TargetedValidationDiscoveryClaimInput,
    assay_evidence: tuple[TargetedValidationAssayEvidenceEntry, ...],
) -> TargetedValidationEntry:
    discovery_direction = _direction_from_effect(claim.discovery_effect_size)
    if not assay_evidence:
        reasons = [
            TargetedValidationReasonCode.SITE_SPECIFIC_VALIDATION_NOT_AVAILABLE
            if claim.candidate_kind is TargetedPanelCandidateKind.PTM_SITE
            else TargetedValidationReasonCode.NOT_ASSAYED_IN_VALIDATION_PANEL
        ]
        verdict = TargetedValidationVerdict.INCONCLUSIVE
        validation_log2_effect = None
        validation_direction = TargetedValidationDirection.UNKNOWN
    else:
        confirmed = sum(
            1
            for entry in assay_evidence
            if entry.verdict is TargetedValidationVerdict.CONFIRMED
        )
        contradicted = sum(
            1
            for entry in assay_evidence
            if entry.verdict is TargetedValidationVerdict.CONTRADICTED
        )
        inconclusive = len(assay_evidence) - confirmed - contradicted
        numeric_effects = sorted(
            entry.validation_log2_effect
            for entry in assay_evidence
            if entry.validation_log2_effect is not None
        )
        validation_log2_effect = (
            None if not numeric_effects else median(numeric_effects)
        )
        validation_direction = _direction_from_effect(validation_log2_effect)

        if confirmed > 0 and contradicted == 0:
            verdict = TargetedValidationVerdict.CONFIRMED
            reasons = [TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY]
        elif contradicted > 0 and confirmed == 0:
            verdict = TargetedValidationVerdict.CONTRADICTED
            reasons = sorted(
                {
                    reason
                    for entry in assay_evidence
                    if entry.verdict is TargetedValidationVerdict.CONTRADICTED
                    for reason in entry.reason_codes
                },
                key=lambda item: item.value,
            )
        elif confirmed > 0 and contradicted > 0:
            verdict = TargetedValidationVerdict.INCONCLUSIVE
            reasons = [TargetedValidationReasonCode.CONFLICTING_VALIDATION_ASSAYS]
        else:
            verdict = TargetedValidationVerdict.INCONCLUSIVE
            reasons = sorted(
                {reason for entry in assay_evidence for reason in entry.reason_codes},
                key=lambda item: item.value,
            )
        return TargetedValidationEntry(
            candidate_id=claim.candidate_id,
            candidate_kind=claim.candidate_kind,
            display_label=claim.display_label,
            target_protein_ref=claim.target_protein_ref,
            site_key=claim.site_key,
            priority_rank=claim.priority_rank,
            discovery_effect_size=claim.discovery_effect_size,
            discovery_direction=discovery_direction,
            validation_log2_effect=validation_log2_effect,
            validation_direction=validation_direction,
            verdict=verdict,
            assay_evidence_count=len(assay_evidence),
            confirmed_assay_count=confirmed,
            contradicted_assay_count=contradicted,
            inconclusive_assay_count=inconclusive,
            reason_codes=_sorted_reason_codes(reasons),
            note=_build_candidate_note(
                claim=claim,
                verdict=verdict,
                reasons=reasons,
                assay_evidence=assay_evidence,
                validation_log2_effect=validation_log2_effect,
            ),
        )

    return TargetedValidationEntry(
        candidate_id=claim.candidate_id,
        candidate_kind=claim.candidate_kind,
        display_label=claim.display_label,
        target_protein_ref=claim.target_protein_ref,
        site_key=claim.site_key,
        priority_rank=claim.priority_rank,
        discovery_effect_size=claim.discovery_effect_size,
        discovery_direction=discovery_direction,
        validation_log2_effect=None,
        validation_direction=TargetedValidationDirection.UNKNOWN,
        verdict=verdict,
        assay_evidence_count=0,
        confirmed_assay_count=0,
        contradicted_assay_count=0,
        inconclusive_assay_count=0,
        reason_codes=_sorted_reason_codes(reasons),
        note=_build_candidate_note(
            claim=claim,
            verdict=verdict,
            reasons=reasons,
            assay_evidence=(),
            validation_log2_effect=None,
        ),
    )


def _match_assay_target_ids(
    assay: TargetedValidationPanelAssayInput,
    descriptors: dict[str, _ImportedTargetDescriptor],
) -> tuple[str, ...]:
    exact = [
        descriptor.target_id
        for descriptor in descriptors.values()
        if descriptor.precursor_charge == assay.precursor_charge
        and descriptor.peptide_sequence == assay.peptide_sequence
        and assay.target_protein_ref in descriptor.protein_refs
    ]
    if exact:
        return tuple(sorted(exact))
    fallback = [
        descriptor.target_id
        for descriptor in descriptors.values()
        if descriptor.precursor_charge == assay.precursor_charge
        and descriptor.peptide_sequence == assay.peptide_sequence
        and not descriptor.protein_refs
    ]
    return tuple(sorted(fallback))


def _collect_condition_log2_intensities(
    *,
    matched_target_id: str,
    target_qc_by_target_sample: dict[tuple[str, str], TargetedTargetQcEntry],
    condition_by_sample: dict[str, str],
    policy: TargetedResultValidationPolicy,
) -> tuple[list[float], list[float]]:
    case_values: list[float] = []
    control_values: list[float] = []
    for (target_id, sample_id), entry in target_qc_by_target_sample.items():
        if target_id != matched_target_id or not entry.reliable:
            continue
        if (
            entry.passing_total_intensity is None
            or entry.passing_total_intensity <= 0.0
        ):
            continue
        condition = condition_by_sample.get(sample_id)
        if condition == policy.case_condition:
            case_values.append(math.log2(entry.passing_total_intensity))
        elif condition == policy.control_condition:
            control_values.append(math.log2(entry.passing_total_intensity))
    return case_values, control_values


def _direction_from_effect(
    effect_size: float | None,
    *,
    flat_threshold: float = 0.0,
) -> TargetedValidationDirection:
    if effect_size is None:
        return TargetedValidationDirection.UNKNOWN
    if abs(effect_size) <= flat_threshold:
        return TargetedValidationDirection.FLAT
    return (
        TargetedValidationDirection.UP
        if effect_size > 0.0
        else TargetedValidationDirection.DOWN
    )


def _evidence_verdict_from_reasons(
    reasons: list[TargetedValidationReasonCode],
) -> TargetedValidationVerdict:
    reason_set = set(reasons)
    if TargetedValidationReasonCode.VALIDATION_EFFECT_MATCHES_DISCOVERY in reason_set:
        return TargetedValidationVerdict.CONFIRMED
    if reason_set.intersection(
        {
            TargetedValidationReasonCode.VALIDATION_EFFECT_OPPOSES_DISCOVERY,
            TargetedValidationReasonCode.VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY,
        }
    ):
        return TargetedValidationVerdict.CONTRADICTED
    return TargetedValidationVerdict.INCONCLUSIVE


def _build_assay_note(
    *,
    verdict: TargetedValidationVerdict,
    assay: TargetedValidationPanelAssayInput,
    reasons: list[TargetedValidationReasonCode],
    policy: TargetedResultValidationPolicy,
    case_reliable_sample_count: int,
    control_reliable_sample_count: int,
    validation_log2_effect: float | None,
) -> str:
    if verdict is TargetedValidationVerdict.CONFIRMED:
        return (
            f"unique targeted assay {assay.assay_entry_id} matched the discovery direction "
            f"with {case_reliable_sample_count} reliable {policy.case_condition} samples and "
            f"{control_reliable_sample_count} reliable {policy.control_condition} samples"
        )
    if TargetedValidationReasonCode.VALIDATION_EFFECT_OPPOSES_DISCOVERY in reasons:
        return f"targeted assay {assay.assay_entry_id} opposed the discovery direction under reliable sample support"
    if TargetedValidationReasonCode.VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY in reasons:
        return f"targeted assay {assay.assay_entry_id} stayed near-flat despite the discovery effect, keeping the conflict explicit"
    if TargetedValidationReasonCode.NON_UNIQUE_VALIDATION_ASSAY in reasons:
        return f"targeted assay {assay.assay_entry_id} uses a {assay.uniqueness_class.value} peptide and cannot confirm one specific protein claim"
    if TargetedValidationReasonCode.INSUFFICIENT_RELIABLE_REPLICATES in reasons:
        return f"targeted assay {assay.assay_entry_id} lacks enough reliable {policy.case_condition} and {policy.control_condition} replicates for a directional validation call"
    if TargetedValidationReasonCode.AMBIGUOUS_TARGETED_RESULT_MAPPING in reasons:
        return f"targeted assay {assay.assay_entry_id} matched multiple imported precursor targets and stays inconclusive"
    if TargetedValidationReasonCode.NO_MATCHING_TARGETED_SIGNAL in reasons:
        return f"targeted assay {assay.assay_entry_id} could not be matched back onto the imported targeted result bundle"
    if (
        TargetedValidationReasonCode.WEAK_VALIDATION_EFFECT in reasons
        and validation_log2_effect is not None
    ):
        return f"targeted assay {assay.assay_entry_id} moved in the expected direction but only by {validation_log2_effect:.2f} log2 units, below the validation threshold"
    if TargetedValidationReasonCode.DISCOVERY_DIRECTION_MISSING in reasons:
        return f"discovery claim for {assay.target_protein_ref} did not preserve a directional effect, so targeted evidence remains advisory only"
    return assay.warning_note


def _build_candidate_note(
    *,
    claim: TargetedValidationDiscoveryClaimInput,
    verdict: TargetedValidationVerdict,
    reasons: list[TargetedValidationReasonCode],
    assay_evidence: tuple[TargetedValidationAssayEvidenceEntry, ...],
    validation_log2_effect: float | None,
) -> str:
    if verdict is TargetedValidationVerdict.CONFIRMED:
        return (
            f"targeted validation confirmed the discovery claim for {claim.display_label}"
            + (
                ""
                if validation_log2_effect is None
                else f" with a median targeted effect of {validation_log2_effect:.2f} log2 units"
            )
        )
    if verdict is TargetedValidationVerdict.CONTRADICTED:
        if TargetedValidationReasonCode.VALIDATION_EFFECT_OPPOSES_DISCOVERY in reasons:
            return f"targeted validation contradicted the discovery direction for {claim.display_label}"
        if (
            TargetedValidationReasonCode.VALIDATION_EFFECT_FLAT_AGAINST_DISCOVERY
            in reasons
        ):
            return f"targeted validation stayed flat for {claim.display_label} despite the discovery claim"
    if TargetedValidationReasonCode.CONFLICTING_VALIDATION_ASSAYS in reasons:
        return f"targeted assays for {claim.display_label} disagree with one another, so the conflict remains explicit instead of being hidden"
    if TargetedValidationReasonCode.SITE_SPECIFIC_VALIDATION_NOT_AVAILABLE in reasons:
        return f"{claim.display_label} remains inconclusive because the discovery candidate is site-specific and no site-specific targeted assay was carried into the validation panel"
    if TargetedValidationReasonCode.NOT_ASSAYED_IN_VALIDATION_PANEL in reasons:
        return f"{claim.display_label} was not represented in the targeted validation panel and therefore stays inconclusive"
    if assay_evidence:
        return f"targeted validation for {claim.display_label} remained inconclusive because no assay produced enough specific and reliable evidence for a confirmation or contradiction call"
    return claim.ranking_note


def _sorted_reason_codes(
    reasons: list[TargetedValidationReasonCode],
) -> tuple[TargetedValidationReasonCode, ...]:
    return tuple(sorted(set(reasons), key=lambda item: item.value))


__all__ = [
    "TargetedResultValidationPolicy",
    "TargetedResultValidationReport",
    "TargetedResultValidationSummary",
    "TargetedValidationAssayEvidenceEntry",
    "TargetedValidationDirection",
    "TargetedValidationDiscoveryClaimInput",
    "TargetedValidationEntry",
    "TargetedValidationPanelAssayInput",
    "TargetedValidationReasonCode",
    "TargetedValidationVerdict",
    "build_targeted_result_validation_report",
    "render_targeted_result_validation_evidence_tsv",
    "render_targeted_result_validation_summary_tsv",
    "render_targeted_result_validation_tsv",
]
