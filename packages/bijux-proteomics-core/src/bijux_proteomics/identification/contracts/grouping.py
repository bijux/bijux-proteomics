# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Protein grouping and shared-peptide ambiguity contracts."""

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

from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    TargetDecoyState,
)
from bijux_proteomics.domain.records import (
    ModifiedPeptide as CanonicalModifiedPeptide,
)
from bijux_proteomics.domain.records import (
    PeptideRecord as CanonicalPeptideRecord,
)
from bijux_proteomics.domain.records import (
    ProteinGroup as CanonicalProteinGroup,
)
from bijux_proteomics.domain.records import (
    ProteinRecord as CanonicalProteinRecord,
)
from bijux_proteomics.domain.records import (
    PSMRecord as CanonicalPsmRecord,
)
from bijux_proteomics.domain.records import (
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics.identification.contracts.evidence import rollup_peptide_evidence
from bijux_proteomics.identification.contracts.psm import PsmRecord, TargetDecoyLabel
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class SharedPeptideAmbiguityReason(StrEnum):
    """Reason a protein group remains ambiguous."""

    INDISTINGUISHABLE_MEMBERS = "indistinguishable_members"
    EXTERNAL_SHARED_PEPTIDES = "external_shared_peptides"
    MIXED = "mixed"


class ProteinGroupEntry(JsonModel):
    """One indistinguishable protein group from shared peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel

    def to_domain_record(self) -> CanonicalProteinGroup:
        """Convert one identification-local protein group into the canonical record."""

        return CanonicalProteinGroup(
            group_id=self.group_id,
            representative_protein=self.representative_protein,
            protein_refs=self.protein_refs,
            peptides=self.peptides,
            unique_peptide_count=self.unique_peptide_count,
            shared_peptide_count=self.shared_peptide_count,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={"source_contract": "identification.protein_group"},
        )


class SharedPeptideAmbiguityEntry(JsonModel):
    """Explanation for why a protein group remains ambiguous."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    outside_group_proteins: tuple[str, ...] = Field(default_factory=tuple)
    reason: SharedPeptideAmbiguityReason
    explanation: str = Field(..., min_length=1)


class SharedPeptideAmbiguityReport(JsonModel):
    """Ambiguity explanations over the protein groups implied by peptide sharing."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[SharedPeptideAmbiguityEntry, ...] = Field(default_factory=tuple)


class RazorPeptideAssignment(JsonModel):
    """One peptide-to-protein assignment under a razor policy."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    assigned_protein: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class RazorPeptideProvenanceEntry(JsonModel):
    """Audit-friendly evidence for one razor peptide assignment."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    assigned_protein: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    candidate_unique_peptide_counts: dict[str, int] = Field(default_factory=dict)
    candidate_best_scores: dict[str, float] = Field(default_factory=dict)


class RazorPeptideProvenanceReport(JsonModel):
    """Razor assignment policy plus per-peptide audit evidence."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(..., min_length=1)
    tie_break_order: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[RazorPeptideProvenanceEntry, ...] = Field(default_factory=tuple)


def build_protein_groups(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinGroupEntry, ...]:
    """Group indistinguishable proteins by their peptide evidence sets."""
    from bijux_proteomics.identification.protein_grouping import (
        build_protein_grouping_report,
    )

    report = build_protein_grouping_report(records)
    return tuple(
        ProteinGroupEntry(
            group_id=group.group_id,
            representative_protein=group.representative_protein,
            protein_refs=group.protein_refs,
            peptides=group.peptides,
            unique_peptide_count=group.unique_peptide_count,
            shared_peptide_count=group.shared_peptide_count,
            best_score=group.best_score,
            best_q_value=group.best_q_value,
            target_decoy_label=group.target_decoy_label,
        )
        for group in report.groups
    )


def build_shared_peptide_ambiguity_report(
    records: tuple[PsmRecord, ...],
) -> SharedPeptideAmbiguityReport:
    """Explain why protein groups remain ambiguous under shared peptide evidence."""
    peptide_rollups = {
        rollup.canonical_peptide: rollup for rollup in rollup_peptide_evidence(records)
    }
    entries: list[SharedPeptideAmbiguityEntry] = []
    for group in build_protein_groups(records):
        shared_peptides = tuple(
            sorted(
                peptide
                for peptide in group.peptides
                if len(peptide_rollups[peptide].protein_refs) > 1
            )
        )
        if not shared_peptides and len(group.protein_refs) == 1:
            continue
        unique_peptides = tuple(
            sorted(
                peptide
                for peptide in group.peptides
                if len(peptide_rollups[peptide].protein_refs) == 1
            )
        )
        outside_group_proteins = tuple(
            sorted(
                {
                    protein_ref
                    for peptide in shared_peptides
                    for protein_ref in peptide_rollups[peptide].protein_refs
                    if protein_ref not in group.protein_refs
                }
            )
        )
        if len(group.protein_refs) > 1 and outside_group_proteins:
            reason = SharedPeptideAmbiguityReason.MIXED
            explanation = f"group {group.group_id} has indistinguishable members and shared peptides that also map outside the group"
        elif len(group.protein_refs) > 1:
            reason = SharedPeptideAmbiguityReason.INDISTINGUISHABLE_MEMBERS
            explanation = f"group {group.group_id} contains proteins with the same observed peptide evidence"
        else:
            reason = SharedPeptideAmbiguityReason.EXTERNAL_SHARED_PEPTIDES
            explanation = f"group {group.group_id} is connected to outside proteins only through shared peptide evidence"
        entries.append(
            SharedPeptideAmbiguityEntry(
                group_id=group.group_id,
                protein_refs=group.protein_refs,
                shared_peptides=shared_peptides,
                unique_peptides=unique_peptides,
                outside_group_proteins=outside_group_proteins,
                reason=reason,
                explanation=explanation,
            )
        )
    return SharedPeptideAmbiguityReport(entries=tuple(entries))


def assign_razor_peptides(
    records: tuple[PsmRecord, ...],
) -> tuple[RazorPeptideAssignment, ...]:
    """Assign shared peptides to one representative protein by razor rules."""
    peptide_rollups = rollup_peptide_evidence(records)
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1

    assignments: list[RazorPeptideAssignment] = []
    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        candidates = tuple(sorted(rollup.protein_refs))
        if not candidates:
            continue
        rationale = "unique_peptide"
        assigned = candidates[0]
        if len(candidates) > 1:
            ranked = sorted(
                candidates,
                key=lambda protein_ref: (
                    -unique_counts.get(protein_ref, 0),
                    -best_scores.get(protein_ref, float("-inf")),
                    protein_ref,
                ),
            )
            assigned = ranked[0]
            if unique_counts.get(ranked[0], 0) != unique_counts.get(ranked[-1], 0):
                rationale = "unique_evidence_priority"
            elif best_scores.get(ranked[0], 0.0) != best_scores.get(ranked[-1], 0.0):
                rationale = "best_score_tiebreak"
            else:
                rationale = "lexicographic_tiebreak"
        assignments.append(
            RazorPeptideAssignment(
                canonical_peptide=rollup.canonical_peptide,
                candidate_proteins=candidates,
                assigned_protein=assigned,
                rationale=rationale,
            )
        )
    return tuple(assignments)


def build_razor_peptide_provenance_report(
    records: tuple[PsmRecord, ...],
) -> RazorPeptideProvenanceReport:
    """Build an explicit provenance report for razor peptide assignments."""
    peptide_rollups = rollup_peptide_evidence(records)
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1

    assignments = {
        entry.canonical_peptide: entry for entry in assign_razor_peptides(records)
    }
    entries: list[RazorPeptideProvenanceEntry] = []
    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        assignment = assignments.get(rollup.canonical_peptide)
        if assignment is None:
            continue
        entries.append(
            RazorPeptideProvenanceEntry(
                canonical_peptide=rollup.canonical_peptide,
                candidate_proteins=assignment.candidate_proteins,
                assigned_protein=assignment.assigned_protein,
                rationale=assignment.rationale,
                candidate_unique_peptide_counts={
                    protein_ref: unique_counts.get(protein_ref, 0)
                    for protein_ref in assignment.candidate_proteins
                },
                candidate_best_scores={
                    protein_ref: best_scores.get(protein_ref, 0.0)
                    for protein_ref in assignment.candidate_proteins
                },
            )
        )
    return RazorPeptideProvenanceReport(
        policy_name="unique_peptide_then_best_score_then_lexicographic",
        tie_break_order=(
            "unique_peptide_count",
            "best_score",
            "protein_accession",
        ),
        entries=tuple(entries),
    )


__all__ = [
    "SharedPeptideAmbiguityReason",
    "ProteinGroupEntry",
    "SharedPeptideAmbiguityEntry",
    "SharedPeptideAmbiguityReport",
    "RazorPeptideAssignment",
    "RazorPeptideProvenanceEntry",
    "RazorPeptideProvenanceReport",
    "build_protein_groups",
    "build_shared_peptide_ambiguity_report",
    "assign_razor_peptides",
    "build_razor_peptide_provenance_report",
]
