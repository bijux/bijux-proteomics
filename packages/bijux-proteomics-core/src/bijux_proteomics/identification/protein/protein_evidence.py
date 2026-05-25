# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein evidence tiering over grouped protein support."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.peptide.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
    RunDetectionContext,
    build_protein_cross_run_reproducibility_report,
)
from bijux_proteomics.identification.peptide.peptide_evidence import (
    PeptideEvidenceClass,
    build_peptide_evidence_report,
)
from bijux_proteomics.identification.protein.protein_grouping import (
    ProteinGroupingEntry,
    build_protein_grouping_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinEvidenceTier(StrEnum):
    """Durable evidence tiers over final protein groups."""

    HIGH_CONFIDENCE = "high_confidence"
    MODERATE = "moderate"
    WEAK = "weak"
    AMBIGUOUS = "ambiguous"
    CONTAMINANT = "contaminant"
    DECOY = "decoy"


class ProteinEvidenceDowngradeReason(StrEnum):
    """Explicit reasons why a protein group could not remain top tier."""

    GROUP_Q_VALUE_ABOVE_HIGH_CONFIDENCE = "group_q_value_above_high_confidence"
    GROUP_Q_VALUE_ABOVE_MODERATE = "group_q_value_above_moderate"
    SHARED_PEPTIDE_ONLY = "shared_peptide_only"
    MODERATE_UNIQUE_PEPTIDE_SUPPORT = "moderate_unique_peptide_support"
    WEAK_OR_AMBIGUOUS_UNIQUE_PEPTIDE_SUPPORT = "weak_or_ambiguous_unique_peptide_support"
    SINGLE_RUN_ONLY = "single_run_only"
    CONTAMINANT_SUPPORT = "contaminant_support"
    DECOY_SUPPORT = "decoy_support"


class ProteinEvidenceEntry(JsonModel):
    """One owned protein evidence row."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    leading_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    evidence_tier: ProteinEvidenceTier
    downgrade_reasons: tuple[ProteinEvidenceDowngradeReason, ...] = Field(
        default_factory=tuple
    )
    representative_reproducibility_class: CrossRunReproducibilityClass | None = None
    exploratory_override: bool = False
    detected_run_count: int = Field(..., ge=0)
    detection_frequency: float = Field(..., ge=0.0, le=1.0)
    replicate_consistency: float = Field(..., ge=0.0, le=1.0)
    condition_specificity: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False
    explanation: str = Field(..., min_length=1)


class ProteinEvidenceSummary(JsonModel):
    """Compact tier summary over grouped protein evidence."""

    model_config = ConfigDict(extra="forbid")

    total_groups: int = Field(..., ge=0)
    high_confidence_count: int = Field(..., ge=0)
    moderate_count: int = Field(..., ge=0)
    weak_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)
    contaminant_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    shared_peptide_only_count: int = Field(..., ge=0)
    single_run_only_count: int = Field(..., ge=0)


class ProteinEvidenceReport(JsonModel):
    """Owned final protein evidence packet."""

    model_config = ConfigDict(extra="forbid")

    high_q_value: float = Field(..., ge=0.0)
    moderate_q_value: float = Field(..., ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    run_context_count: int = Field(..., ge=0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    summary: ProteinEvidenceSummary
    entries: tuple[ProteinEvidenceEntry, ...] = Field(default_factory=tuple)


def build_protein_evidence_report(
    records: tuple[PsmRecord, ...],
    *,
    high_q_value: float = 0.01,
    moderate_q_value: float = 0.05,
    score_orientation: str = "higher_better",
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_protein_refs: tuple[str, ...] = (),
) -> ProteinEvidenceReport:
    """Build one owned protein evidence report over grouped protein support."""
    if high_q_value < 0.0 or moderate_q_value < 0.0:
        raise ValueError("protein evidence thresholds must be non-negative")
    if high_q_value > moderate_q_value:
        raise ValueError("high_q_value must not exceed moderate_q_value")

    grouping_report = build_protein_grouping_report(records)
    exploratory_protein_ref_set = set(exploratory_protein_refs)
    exploratory_canonical_peptides = tuple(
        sorted(
            {
                record.canonical_peptide
                for record in records
                if record.protein_refs
                and set(record.protein_refs).issubset(exploratory_protein_ref_set)
            }
        )
    )
    peptide_evidence = build_peptide_evidence_report(
        records,
        threshold=moderate_q_value,
        score_orientation=score_orientation,
        strong_q_value=high_q_value,
        run_contexts=run_contexts,
        exploratory_canonical_peptides=exploratory_canonical_peptides,
    )
    peptide_by_sequence = {
        entry.canonical_peptide: entry for entry in peptide_evidence.entries
    }
    reproducibility_report = build_protein_cross_run_reproducibility_report(
        records,
        run_contexts=run_contexts,
        exploratory_protein_refs=exploratory_protein_refs,
    )
    reproducibility_by_protein = {
        entry.entity_id: entry for entry in reproducibility_report.entries
    }

    entries = tuple(
        sorted(
            (
                _build_entry(
                    group=group,
                    peptide_by_sequence=peptide_by_sequence,
                    reproducibility_by_protein=reproducibility_by_protein,
                    high_q_value=high_q_value,
                    moderate_q_value=moderate_q_value,
                )
                for group in grouping_report.groups
            ),
            key=lambda entry: entry.group_id,
        )
    )
    payload = {
        "high_q_value": high_q_value,
        "moderate_q_value": moderate_q_value,
        "score_orientation": score_orientation,
        "run_contexts": [context.to_dict() for context in run_contexts],
        "exploratory_protein_refs": list(exploratory_protein_refs),
        "entries": [entry.to_dict() for entry in entries],
    }
    return ProteinEvidenceReport(
        high_q_value=high_q_value,
        moderate_q_value=moderate_q_value,
        score_orientation=score_orientation,
        run_context_count=len(run_contexts),
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        summary=ProteinEvidenceSummary(
            total_groups=len(entries),
            high_confidence_count=sum(
                1
                for entry in entries
                if entry.evidence_tier is ProteinEvidenceTier.HIGH_CONFIDENCE
            ),
            moderate_count=sum(
                1
                for entry in entries
                if entry.evidence_tier is ProteinEvidenceTier.MODERATE
            ),
            weak_count=sum(
                1 for entry in entries if entry.evidence_tier is ProteinEvidenceTier.WEAK
            ),
            ambiguous_count=sum(
                1
                for entry in entries
                if entry.evidence_tier is ProteinEvidenceTier.AMBIGUOUS
            ),
            contaminant_count=sum(
                1
                for entry in entries
                if entry.evidence_tier is ProteinEvidenceTier.CONTAMINANT
            ),
            decoy_count=sum(
                1
                for entry in entries
                if entry.evidence_tier is ProteinEvidenceTier.DECOY
            ),
            shared_peptide_only_count=sum(
                1
                for entry in entries
                if ProteinEvidenceDowngradeReason.SHARED_PEPTIDE_ONLY
                in entry.downgrade_reasons
            ),
            single_run_only_count=sum(
                1
                for entry in entries
                if ProteinEvidenceDowngradeReason.SINGLE_RUN_ONLY
                in entry.downgrade_reasons
            ),
        ),
        entries=entries,
    )


def render_protein_evidence_summary_tsv(report: ProteinEvidenceReport) -> str:
    """Render the protein evidence summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("high_q_value", report.high_q_value),
        ("moderate_q_value", report.moderate_q_value),
        ("score_orientation", report.score_orientation),
        ("run_context_count", report.run_context_count),
        ("reproducibility_hash", report.reproducibility_hash),
        ("total_groups", report.summary.total_groups),
        ("high_confidence_count", report.summary.high_confidence_count),
        ("moderate_count", report.summary.moderate_count),
        ("weak_count", report.summary.weak_count),
        ("ambiguous_count", report.summary.ambiguous_count),
        ("contaminant_count", report.summary.contaminant_count),
        ("decoy_count", report.summary.decoy_count),
        ("shared_peptide_only_count", report.summary.shared_peptide_only_count),
        ("single_run_only_count", report.summary.single_run_only_count),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_evidence_entries_tsv(report: ProteinEvidenceReport) -> str:
    """Render the final protein evidence rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "group_id",
            "representative_protein",
            "leading_protein",
            "protein_refs",
            "peptides",
            "unique_peptides",
            "shared_peptides",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "best_score",
            "best_q_value",
            "evidence_tier",
            "downgrade_reasons",
            "representative_reproducibility_class",
            "exploratory_override",
            "detected_run_count",
            "detection_frequency",
            "replicate_consistency",
            "condition_specificity",
            "target_decoy_label",
            "contaminant_flag",
            "explanation",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.group_id,
                entry.representative_protein,
                entry.leading_protein,
                ";".join(entry.protein_refs),
                ";".join(entry.peptides),
                ";".join(entry.unique_peptides),
                ";".join(entry.shared_peptides),
                entry.peptide_count,
                entry.unique_peptide_count,
                entry.shared_peptide_count,
                entry.best_score,
                "" if entry.best_q_value is None else entry.best_q_value,
                entry.evidence_tier.value,
                ";".join(reason.value for reason in entry.downgrade_reasons),
                ""
                if entry.representative_reproducibility_class is None
                else entry.representative_reproducibility_class.value,
                str(entry.exploratory_override).lower(),
                entry.detected_run_count,
                entry.detection_frequency,
                entry.replicate_consistency,
                entry.condition_specificity,
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
                entry.explanation,
            )
        )
    return buffer.getvalue()


def _build_entry(
    *,
    group: ProteinGroupingEntry,
    peptide_by_sequence: dict[str, object],
    reproducibility_by_protein: dict[str, object],
    high_q_value: float,
    moderate_q_value: float,
) -> ProteinEvidenceEntry:
    unique_entries = tuple(
        peptide_by_sequence[peptide]
        for peptide in group.unique_peptides
        if peptide in peptide_by_sequence
    )
    reproducibility = reproducibility_by_protein.get(group.representative_protein)
    evidence_tier, downgrade_reasons = _classify_group(
        group=group,
        unique_entries=unique_entries,
        reproducibility_class=None
        if reproducibility is None
        else reproducibility.reproducibility_class,
        exploratory_override=False if reproducibility is None else reproducibility.exploratory_override,
        high_q_value=high_q_value,
        moderate_q_value=moderate_q_value,
    )
    return ProteinEvidenceEntry(
        group_id=group.group_id,
        representative_protein=group.representative_protein,
        leading_protein=group.leading_protein,
        protein_refs=group.protein_refs,
        peptides=group.peptides,
        unique_peptides=group.unique_peptides,
        shared_peptides=group.shared_peptides,
        peptide_count=group.peptide_count,
        unique_peptide_count=group.unique_peptide_count,
        shared_peptide_count=group.shared_peptide_count,
        best_score=group.best_score,
        best_q_value=group.best_q_value,
        evidence_tier=evidence_tier,
        downgrade_reasons=downgrade_reasons,
        representative_reproducibility_class=None
        if reproducibility is None
        else reproducibility.reproducibility_class,
        exploratory_override=False if reproducibility is None else reproducibility.exploratory_override,
        detected_run_count=0 if reproducibility is None else reproducibility.detected_run_count,
        detection_frequency=0.0 if reproducibility is None else reproducibility.detection_frequency,
        replicate_consistency=0.0 if reproducibility is None else reproducibility.replicate_consistency,
        condition_specificity=0.0 if reproducibility is None else reproducibility.condition_specificity,
        target_decoy_label=group.target_decoy_label,
        contaminant_flag=group.contaminant_flag,
        explanation=_build_explanation(evidence_tier, downgrade_reasons),
    )


def _classify_group(
    *,
    group: ProteinGroupingEntry,
    unique_entries: tuple[object, ...],
    reproducibility_class: CrossRunReproducibilityClass | None,
    exploratory_override: bool,
    high_q_value: float,
    moderate_q_value: float,
) -> tuple[ProteinEvidenceTier, tuple[ProteinEvidenceDowngradeReason, ...]]:
    if group.target_decoy_label is TargetDecoyLabel.DECOY:
        return (
            ProteinEvidenceTier.DECOY,
            (ProteinEvidenceDowngradeReason.DECOY_SUPPORT,),
        )
    if group.contaminant_flag:
        return (
            ProteinEvidenceTier.CONTAMINANT,
            (ProteinEvidenceDowngradeReason.CONTAMINANT_SUPPORT,),
        )

    reasons: list[ProteinEvidenceDowngradeReason] = []
    q_value = group.best_q_value if group.best_q_value is not None else 1.0
    if group.unique_peptide_count == 0 and group.shared_peptide_count > 0:
        return (
            ProteinEvidenceTier.AMBIGUOUS,
            (ProteinEvidenceDowngradeReason.SHARED_PEPTIDE_ONLY,),
        )

    tier = _tier_from_q_value(
        q_value=q_value,
        high_q_value=high_q_value,
        moderate_q_value=moderate_q_value,
    )
    if q_value > high_q_value:
        reasons.append(ProteinEvidenceDowngradeReason.GROUP_Q_VALUE_ABOVE_HIGH_CONFIDENCE)
    if q_value > moderate_q_value:
        reasons.append(ProteinEvidenceDowngradeReason.GROUP_Q_VALUE_ABOVE_MODERATE)

    unique_classes = {entry.primary_class for entry in unique_entries}
    strong_unique = PeptideEvidenceClass.STRONG in unique_classes
    moderate_unique = PeptideEvidenceClass.MODERATE in unique_classes
    weak_or_ambiguous_unique = bool(
        unique_classes
        & {
            PeptideEvidenceClass.WEAK,
            PeptideEvidenceClass.AMBIGUOUS,
            PeptideEvidenceClass.SHARED,
        }
    )
    if (
        not strong_unique
        and moderate_unique
        and tier is ProteinEvidenceTier.HIGH_CONFIDENCE
        and reproducibility_class is not CrossRunReproducibilityClass.SINGLE_RUN_ONLY
    ):
        reasons.append(ProteinEvidenceDowngradeReason.MODERATE_UNIQUE_PEPTIDE_SUPPORT)
        tier = ProteinEvidenceTier.MODERATE
    if weak_or_ambiguous_unique and not strong_unique and not moderate_unique:
        reasons.append(
            ProteinEvidenceDowngradeReason.WEAK_OR_AMBIGUOUS_UNIQUE_PEPTIDE_SUPPORT
        )
        tier = ProteinEvidenceTier.WEAK
    if (
        reproducibility_class is CrossRunReproducibilityClass.SINGLE_RUN_ONLY
        and not exploratory_override
    ):
        reasons.append(ProteinEvidenceDowngradeReason.SINGLE_RUN_ONLY)
        if tier is ProteinEvidenceTier.HIGH_CONFIDENCE:
            tier = ProteinEvidenceTier.MODERATE
    return (tier, tuple(dict.fromkeys(reasons)))


def _tier_from_q_value(
    *,
    q_value: float,
    high_q_value: float,
    moderate_q_value: float,
) -> ProteinEvidenceTier:
    if q_value <= high_q_value:
        return ProteinEvidenceTier.HIGH_CONFIDENCE
    if q_value <= moderate_q_value:
        return ProteinEvidenceTier.MODERATE
    return ProteinEvidenceTier.WEAK


def _build_explanation(
    evidence_tier: ProteinEvidenceTier,
    downgrade_reasons: tuple[ProteinEvidenceDowngradeReason, ...],
) -> str:
    if not downgrade_reasons:
        if evidence_tier is ProteinEvidenceTier.HIGH_CONFIDENCE:
            return (
                "group q-value and unique peptide support satisfy the high-confidence threshold and protein evidence policy"
            )
        if evidence_tier is ProteinEvidenceTier.MODERATE:
            return "group remains moderate under the protein evidence policy"
        return "group remains reviewable under the protein evidence policy"
    return "; ".join(_reason_message(reason) for reason in downgrade_reasons)


def _reason_message(reason: ProteinEvidenceDowngradeReason) -> str:
    return {
        ProteinEvidenceDowngradeReason.GROUP_Q_VALUE_ABOVE_HIGH_CONFIDENCE: (
            "group q-value is above the high-confidence threshold"
        ),
        ProteinEvidenceDowngradeReason.GROUP_Q_VALUE_ABOVE_MODERATE: (
            "group q-value is above the moderate threshold"
        ),
        ProteinEvidenceDowngradeReason.SHARED_PEPTIDE_ONLY: (
            "group is supported only by shared peptides and cannot support a protein-specific high-confidence call"
        ),
        ProteinEvidenceDowngradeReason.MODERATE_UNIQUE_PEPTIDE_SUPPORT: (
            "unique peptide support is accepted but not strong enough for a high-confidence protein call"
        ),
        ProteinEvidenceDowngradeReason.WEAK_OR_AMBIGUOUS_UNIQUE_PEPTIDE_SUPPORT: (
            "unique peptide support remains weak or ambiguous"
        ),
        ProteinEvidenceDowngradeReason.SINGLE_RUN_ONLY: (
            "representative protein is observed in one run only and is not explicitly exploratory"
        ),
        ProteinEvidenceDowngradeReason.CONTAMINANT_SUPPORT: (
            "group is supported by contaminant proteins"
        ),
        ProteinEvidenceDowngradeReason.DECOY_SUPPORT: (
            "group is supported by decoy proteins"
        ),
    }[reason]
