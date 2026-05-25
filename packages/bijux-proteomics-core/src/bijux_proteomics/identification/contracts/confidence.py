# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Confidence calibration and threshold sensitivity contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.fdr_levels import (
    FdrEvidenceLevel,
    FdrLevelEntry,
    calculate_level_specific_fdr,
)
from bijux_proteomics.identification.contracts.protein_review import (
    PickedProteinFdrEntry,
    calculate_picked_protein_fdr,
)
from bijux_proteomics.identification.contracts.psm import PsmRecord, TargetDecoyLabel
class ConfidenceLabel(StrEnum):
    """Stable confidence labels over q-valued evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"
    DECOY = "decoy"

class ConfidenceAssignment(JsonModel):
    """Confidence label plus its explanation."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0)
    label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)



class LevelSpecificConfidenceAssignment(JsonModel):
    """Confidence assignment for one explicit evidence level."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0)
    label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class LevelSpecificConfidenceReport(JsonModel):
    """Separate confidence assignments for PSM, peptide, and protein levels."""

    model_config = ConfigDict(extra="forbid")

    psm_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )
    peptide_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )
    protein_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )


class ConfidenceThresholdSensitivityEntry(JsonModel):
    """Accepted-entity changes at one explicit confidence threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0, le=1.0)
    accepted_psm_count: int = Field(..., ge=0)
    accepted_peptide_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    accepted_picked_protein_count: int = Field(..., ge=0)
    newly_accepted_psm_ids: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_proteins: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_picked_proteins: tuple[str, ...] = Field(default_factory=tuple)


class ConfidenceThresholdSensitivityReport(JsonModel):
    """Sensitivity report over explicit FDR acceptance thresholds."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    entries: tuple[ConfidenceThresholdSensitivityEntry, ...] = Field(
        default_factory=tuple
    )


class GroupedConfidenceEntry(JsonModel):
    """Confidence summary for one indistinguishable protein group."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_q_value: float | None = Field(default=None, ge=0.0)
    evidence_tier: str = Field(
        ...,
        pattern="^(high_confidence|moderate|weak|ambiguous|contaminant|decoy)$",
    )
    downgrade_reasons: tuple[str, ...] = Field(default_factory=tuple)
    confidence_label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class GroupedConfidenceReport(JsonModel):
    """Grouped confidence view over protein families and indistinguishable groups."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[GroupedConfidenceEntry, ...] = Field(default_factory=tuple)


def assign_confidence_labels(
    entries: tuple[PickedProteinFdrEntry, ...],
    *,
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> tuple[ConfidenceAssignment, ...]:
    """Assign high/medium/low confidence labels from q-valued protein evidence."""
    assignments: list[ConfidenceAssignment] = []
    for entry in entries:
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = "decoy evidence is never promoted to biological confidence"
        elif entry.q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"q-value {entry.q_value:.4f} is at or below the high-confidence threshold"
        elif entry.q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"q-value {entry.q_value:.4f} is at or below the medium-confidence threshold"
        elif entry.accepted:
            label = ConfidenceLabel.LOW
            explanation = f"q-value {entry.q_value:.4f} passes FDR but misses the medium-confidence threshold"
        else:
            label = ConfidenceLabel.REJECTED
            explanation = f"q-value {entry.q_value:.4f} does not pass the requested acceptance threshold"
        assignments.append(
            ConfidenceAssignment(
                entity_id=entry.protein_ref,
                q_value=entry.q_value,
                label=label,
                explanation=explanation,
            )
        )
    return tuple(assignments)


def build_grouped_confidence_report(
    records: tuple[PsmRecord, ...],
    *,
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_protein_refs: tuple[str, ...] = (),
) -> GroupedConfidenceReport:
    """Summarize confidence over indistinguishable protein groups."""
    from bijux_proteomics.identification.protein_evidence import (
        build_protein_evidence_report,
    )

    protein_evidence = build_protein_evidence_report(
        records,
        high_q_value=high_threshold,
        moderate_q_value=medium_threshold,
        score_orientation="higher_better",
        run_contexts=run_contexts,
        exploratory_protein_refs=exploratory_protein_refs,
    )
    entries = [
        GroupedConfidenceEntry(
            group_id=entry.group_id,
            representative_protein=entry.representative_protein,
            protein_refs=entry.protein_refs,
            peptide_count=entry.peptide_count,
            unique_peptide_count=entry.unique_peptide_count,
            shared_peptide_count=entry.shared_peptide_count,
            best_q_value=entry.best_q_value,
            evidence_tier=entry.evidence_tier.value,
            downgrade_reasons=tuple(
                reason.value for reason in entry.downgrade_reasons
            ),
            confidence_label=_map_protein_evidence_tier_to_confidence_label(
                entry.evidence_tier.value
            ),
            explanation=entry.explanation,
        )
        for entry in protein_evidence.entries
    ]
    return GroupedConfidenceReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.group_id))
    )


def _map_protein_evidence_tier_to_confidence_label(
    evidence_tier: str,
) -> ConfidenceLabel:
    if evidence_tier == "high_confidence":
        return ConfidenceLabel.HIGH
    if evidence_tier == "moderate":
        return ConfidenceLabel.MEDIUM
    if evidence_tier == "decoy":
        return ConfidenceLabel.DECOY
    return ConfidenceLabel.LOW


def _assign_level_specific_confidence(
    entries: tuple[FdrLevelEntry, ...],
    *,
    evidence_level: FdrEvidenceLevel,
    high_threshold: float,
    medium_threshold: float,
) -> tuple[LevelSpecificConfidenceAssignment, ...]:
    assignments: list[LevelSpecificConfidenceAssignment] = []
    for entry in entries:
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = "decoy evidence is never promoted to biological confidence"
        elif entry.q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} is at or below the high-confidence threshold"
        elif entry.q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} is at or below the medium-confidence threshold"
        elif entry.accepted:
            label = ConfidenceLabel.LOW
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} passes FDR but misses the medium-confidence threshold"
        else:
            label = ConfidenceLabel.REJECTED
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} does not pass the requested acceptance threshold"
        assignments.append(
            LevelSpecificConfidenceAssignment(
                evidence_level=evidence_level,
                entity_id=entry.entity_id,
                q_value=entry.q_value,
                label=label,
                explanation=explanation,
            )
        )
    return tuple(assignments)


def assign_level_specific_confidence_labels(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = 0.05,
    score_orientation: str = "higher_better",
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> LevelSpecificConfidenceReport:
    """Assign separate confidence labels for PSM, peptide, and protein evidence."""
    level_report = calculate_level_specific_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    return LevelSpecificConfidenceReport(
        psm_assignments=_assign_level_specific_confidence(
            level_report.psm_entries,
            evidence_level=FdrEvidenceLevel.PSM,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
        peptide_assignments=_assign_level_specific_confidence(
            level_report.peptide_entries,
            evidence_level=FdrEvidenceLevel.PEPTIDE,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
        protein_assignments=_assign_level_specific_confidence(
            level_report.protein_entries,
            evidence_level=FdrEvidenceLevel.PROTEIN,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
    )


def build_confidence_threshold_sensitivity_report(
    records: tuple[PsmRecord, ...],
    *,
    thresholds: tuple[float, ...] = (0.001, 0.01, 0.05, 0.1),
    score_orientation: str = "higher_better",
) -> ConfidenceThresholdSensitivityReport:
    """Report how accepted evidence changes across explicit FDR cutoffs."""
    normalized_thresholds = tuple(sorted(dict.fromkeys(thresholds)))
    if any(threshold < 0.0 or threshold > 1.0 for threshold in normalized_thresholds):
        raise ValueError("thresholds must be between 0 and 1")

    entries: list[ConfidenceThresholdSensitivityEntry] = []
    previous_psms: set[str] = set()
    previous_peptides: set[str] = set()
    previous_proteins: set[str] = set()
    previous_picked: set[str] = set()

    for threshold in normalized_thresholds:
        level_report = calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        picked = calculate_picked_protein_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        accepted_psms = {
            entry.entity_id for entry in level_report.psm_entries if entry.accepted
        }
        accepted_peptides = {
            entry.entity_id for entry in level_report.peptide_entries if entry.accepted
        }
        accepted_proteins = {
            entry.entity_id for entry in level_report.protein_entries if entry.accepted
        }
        accepted_picked = {entry.protein_ref for entry in picked if entry.accepted}
        entries.append(
            ConfidenceThresholdSensitivityEntry(
                threshold=threshold,
                accepted_psm_count=len(accepted_psms),
                accepted_peptide_count=len(accepted_peptides),
                accepted_protein_count=len(accepted_proteins),
                accepted_picked_protein_count=len(accepted_picked),
                newly_accepted_psm_ids=tuple(sorted(accepted_psms - previous_psms)),
                newly_accepted_peptides=tuple(
                    sorted(accepted_peptides - previous_peptides)
                ),
                newly_accepted_proteins=tuple(
                    sorted(accepted_proteins - previous_proteins)
                ),
                newly_accepted_picked_proteins=tuple(
                    sorted(accepted_picked - previous_picked)
                ),
            )
        )
        previous_psms = accepted_psms
        previous_peptides = accepted_peptides
        previous_proteins = accepted_proteins
        previous_picked = accepted_picked

    return ConfidenceThresholdSensitivityReport(
        score_orientation=score_orientation,
        thresholds=normalized_thresholds,
        entries=tuple(entries),
    )

__all__ = [
    'ConfidenceLabel',
    'ConfidenceAssignment',
    'GroupedConfidenceEntry',
    'GroupedConfidenceReport',
    'LevelSpecificConfidenceAssignment',
    'LevelSpecificConfidenceReport',
    'ConfidenceThresholdSensitivityEntry',
    'ConfidenceThresholdSensitivityReport',
    'assign_confidence_labels',
    'build_grouped_confidence_report',
    'assign_level_specific_confidence_labels',
    'build_confidence_threshold_sensitivity_report',
]
