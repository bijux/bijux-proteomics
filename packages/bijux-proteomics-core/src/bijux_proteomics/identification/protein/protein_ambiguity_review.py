# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewer-facing reporting over ambiguous protein evidence groups."""

from __future__ import annotations

import csv
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    ConfidenceLabel,
    PsmRecord,
    SharedPeptideAmbiguityReason,
    TargetDecoyLabel,
    build_protein_groups,
    build_shared_peptide_ambiguity_report,
)
from bijux_proteomics.identification.protein.protein_evidence import (
    ProteinEvidenceDowngradeReason,
    ProteinEvidenceTier,
    build_protein_evidence_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinAmbiguityReviewSummary(JsonModel):
    """Compact summary over ambiguous protein groups."""

    model_config = ConfigDict(extra="forbid")

    total_ambiguity_groups: int = Field(..., ge=0)
    ambiguous_protein_count: int = Field(..., ge=0)
    indistinguishable_group_count: int = Field(..., ge=0)
    external_shared_group_count: int = Field(..., ge=0)
    mixed_group_count: int = Field(..., ge=0)
    high_confidence_group_count: int = Field(..., ge=0)
    medium_confidence_group_count: int = Field(..., ge=0)
    low_confidence_group_count: int = Field(..., ge=0)
    rejected_group_count: int = Field(..., ge=0)
    decoy_group_count: int = Field(..., ge=0)


class ProteinAmbiguityReviewEntry(JsonModel):
    """One ambiguous protein group plus the evidence that keeps it unresolved."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    indistinguishable_proteins: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    outside_group_proteins: tuple[str, ...] = Field(default_factory=tuple)
    ambiguity_reason: SharedPeptideAmbiguityReason
    ambiguity_explanation: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    evidence_tier: ProteinEvidenceTier
    downgrade_reasons: tuple[ProteinEvidenceDowngradeReason, ...] = Field(
        default_factory=tuple
    )
    confidence_label: ConfidenceLabel
    confidence_explanation: str = Field(..., min_length=1)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False


class ProteinAmbiguityReviewReport(JsonModel):
    """One review packet over protein ambiguity that resists overclaiming."""

    model_config = ConfigDict(extra="forbid")

    high_q_value: float = Field(..., ge=0.0)
    medium_q_value: float = Field(..., ge=0.0)
    threshold: float | None = Field(default=None, ge=0.0)
    summary: ProteinAmbiguityReviewSummary
    entries: tuple[ProteinAmbiguityReviewEntry, ...] = Field(default_factory=tuple)


def build_protein_ambiguity_review_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    high_q_value: float = 0.01,
    medium_q_value: float = 0.05,
) -> ProteinAmbiguityReviewReport:
    """Build a direct review packet over ambiguous protein groups only."""
    if high_q_value < 0.0 or medium_q_value < 0.0:
        raise ValueError("confidence thresholds must be non-negative")
    if high_q_value > medium_q_value:
        raise ValueError("high_q_value must not exceed medium_q_value")

    groups_by_id = {entry.group_id: entry for entry in build_protein_groups(records)}
    protein_evidence_by_group = {
        entry.group_id: entry
        for entry in build_protein_evidence_report(
            records,
            high_q_value=high_q_value,
            moderate_q_value=medium_q_value,
        ).entries
    }
    entries: list[ProteinAmbiguityReviewEntry] = []
    for ambiguity in build_shared_peptide_ambiguity_report(records).entries:
        group = groups_by_id[ambiguity.group_id]
        protein_evidence = protein_evidence_by_group[group.group_id]
        confidence_label = _map_protein_evidence_tier_to_confidence_label(
            protein_evidence.evidence_tier
        )
        entries.append(
            ProteinAmbiguityReviewEntry(
                group_id=group.group_id,
                representative_protein=group.representative_protein,
                protein_refs=group.protein_refs,
                indistinguishable_proteins=(
                    group.protein_refs if len(group.protein_refs) > 1 else ()
                ),
                shared_peptides=ambiguity.shared_peptides,
                unique_peptides=ambiguity.unique_peptides,
                outside_group_proteins=ambiguity.outside_group_proteins,
                ambiguity_reason=ambiguity.reason,
                ambiguity_explanation=ambiguity.explanation,
                peptide_count=len(group.peptides),
                unique_peptide_count=group.unique_peptide_count,
                shared_peptide_count=group.shared_peptide_count,
                best_score=group.best_score,
                best_q_value=group.best_q_value,
                evidence_tier=protein_evidence.evidence_tier,
                downgrade_reasons=protein_evidence.downgrade_reasons,
                confidence_label=confidence_label,
                confidence_explanation=protein_evidence.explanation,
                target_decoy_label=group.target_decoy_label,
                contaminant_flag=any(
                    protein_ref.startswith("CON__")
                    for protein_ref in group.protein_refs
                ),
            )
        )

    return ProteinAmbiguityReviewReport(
        high_q_value=high_q_value,
        medium_q_value=medium_q_value,
        threshold=threshold,
        summary=ProteinAmbiguityReviewSummary(
            total_ambiguity_groups=len(entries),
            ambiguous_protein_count=sum(len(entry.protein_refs) for entry in entries),
            indistinguishable_group_count=sum(
                1
                for entry in entries
                if entry.ambiguity_reason
                is SharedPeptideAmbiguityReason.INDISTINGUISHABLE_MEMBERS
            ),
            external_shared_group_count=sum(
                1
                for entry in entries
                if entry.ambiguity_reason
                is SharedPeptideAmbiguityReason.EXTERNAL_SHARED_PEPTIDES
            ),
            mixed_group_count=sum(
                1
                for entry in entries
                if entry.ambiguity_reason is SharedPeptideAmbiguityReason.MIXED
            ),
            high_confidence_group_count=sum(
                1 for entry in entries if entry.confidence_label is ConfidenceLabel.HIGH
            ),
            medium_confidence_group_count=sum(
                1
                for entry in entries
                if entry.confidence_label is ConfidenceLabel.MODERATE
            ),
            low_confidence_group_count=sum(
                1 for entry in entries if entry.confidence_label is ConfidenceLabel.LOW
            ),
            rejected_group_count=sum(
                1
                for entry in entries
                if entry.confidence_label is ConfidenceLabel.REJECTED
            ),
            decoy_group_count=sum(
                1
                for entry in entries
                if entry.confidence_label is ConfidenceLabel.DECOY
            ),
        ),
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (
                    entry.group_id,
                    entry.representative_protein,
                ),
            )
        ),
    )


def render_protein_ambiguity_summary_tsv(report: ProteinAmbiguityReviewReport) -> str:
    """Render protein ambiguity summary counts as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("total_ambiguity_groups", report.summary.total_ambiguity_groups),
        ("ambiguous_protein_count", report.summary.ambiguous_protein_count),
        ("indistinguishable_group_count", report.summary.indistinguishable_group_count),
        ("external_shared_group_count", report.summary.external_shared_group_count),
        ("mixed_group_count", report.summary.mixed_group_count),
        ("high_confidence_group_count", report.summary.high_confidence_group_count),
        ("medium_confidence_group_count", report.summary.medium_confidence_group_count),
        ("low_confidence_group_count", report.summary.low_confidence_group_count),
        ("rejected_group_count", report.summary.rejected_group_count),
        ("decoy_group_count", report.summary.decoy_group_count),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_ambiguity_entries_tsv(report: ProteinAmbiguityReviewReport) -> str:
    """Render one TSV row per ambiguous protein group."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "group_id",
            "representative_protein",
            "protein_refs",
            "indistinguishable_proteins",
            "shared_peptides",
            "unique_peptides",
            "outside_group_proteins",
            "ambiguity_reason",
            "ambiguity_explanation",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "best_score",
            "best_q_value",
            "evidence_tier",
            "downgrade_reasons",
            "confidence_label",
            "confidence_explanation",
            "target_decoy_label",
            "contaminant_flag",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.group_id,
                entry.representative_protein,
                ";".join(entry.protein_refs),
                ";".join(entry.indistinguishable_proteins),
                ";".join(entry.shared_peptides),
                ";".join(entry.unique_peptides),
                ";".join(entry.outside_group_proteins),
                entry.ambiguity_reason.value,
                entry.ambiguity_explanation,
                entry.peptide_count,
                entry.unique_peptide_count,
                entry.shared_peptide_count,
                entry.best_score,
                "" if entry.best_q_value is None else entry.best_q_value,
                entry.evidence_tier.value,
                ";".join(reason.value for reason in entry.downgrade_reasons),
                entry.confidence_label.value,
                entry.confidence_explanation,
                entry.target_decoy_label.value,
                str(entry.contaminant_flag).lower(),
            )
        )
    return buffer.getvalue()


def _map_protein_evidence_tier_to_confidence_label(
    evidence_tier: ProteinEvidenceTier,
) -> ConfidenceLabel:
    if evidence_tier is ProteinEvidenceTier.HIGH_CONFIDENCE:
        return ConfidenceLabel.HIGH
    if evidence_tier is ProteinEvidenceTier.MODERATE:
        return ConfidenceLabel.MODERATE
    if evidence_tier is ProteinEvidenceTier.DECOY:
        return ConfidenceLabel.DECOY
    return ConfidenceLabel.LOW
