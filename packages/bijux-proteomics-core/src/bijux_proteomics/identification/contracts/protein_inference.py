# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Parsimony and protein-inference comparison contracts."""

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
from bijux_proteomics.scientific_tables import (
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
from bijux_proteomics.tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.evidence import rollup_peptide_evidence
from bijux_proteomics.identification.contracts.grouping import assign_razor_peptides
from bijux_proteomics.identification.contracts.psm import PsmRecord, TargetDecoyLabel

class ParsimonyVariant(StrEnum):
    """Named protein-parsimony policies supported by core inference."""

    GREEDY_COVERAGE = "greedy_coverage"
    UNIQUE_EVIDENCE_PRIORITY = "unique_evidence_priority"
    BEST_SCORE_PRIORITY = "best_score_priority"


class ParsimonyProteinEntry(JsonModel):
    """One protein selected by the greedy parsimony inference policy."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    selection_rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    source_group_id: str = Field(..., min_length=1)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class InferenceDisagreementKind(StrEnum):
    """Kinds of inference disagreements surfaced for review."""

    PEPTIDE_ASSIGNMENT = "peptide_assignment"
    PROTEIN_SET = "protein_set"


class InferenceDisagreementEntry(JsonModel):
    """One explicit disagreement between inference strategies."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(..., min_length=1)
    kind: InferenceDisagreementKind
    strategy_assignments: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)


class InferenceDisagreementReport(JsonModel):
    """Review-oriented report of disagreements between inference strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[InferenceDisagreementEntry, ...] = Field(default_factory=tuple)


class ParsimonyVariantResult(JsonModel):
    """Selections produced by one named protein-parsimony policy."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    selected_proteins: tuple[ParsimonyProteinEntry, ...] = Field(default_factory=tuple)


class ParsimonyVariantDifferenceEntry(JsonModel):
    """Difference summary between two named parsimony policies."""

    model_config = ConfigDict(extra="forbid")

    left_variant: ParsimonyVariant
    right_variant: ParsimonyVariant
    first_difference_rank: int | None = Field(default=None, ge=1)
    shared_selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    left_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    right_only_proteins: tuple[str, ...] = Field(default_factory=tuple)


class ParsimonyVariantComparisonReport(JsonModel):
    """Comparison across multiple named parsimony policies."""

    model_config = ConfigDict(extra="forbid")

    results: tuple[ParsimonyVariantResult, ...] = Field(default_factory=tuple)
    differences: tuple[ParsimonyVariantDifferenceEntry, ...] = Field(
        default_factory=tuple
    )



def build_inference_disagreement_report(
    records: tuple[PsmRecord, ...],
    *,
    parsimony_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> InferenceDisagreementReport:
    """Expose disagreements across inference strategies instead of hiding them."""
    peptide_rollups = rollup_peptide_evidence(records)
    razor = {entry.canonical_peptide: entry for entry in assign_razor_peptides(records)}
    parsimony_results = {
        variant: infer_proteins_by_parsimony(records, variant=variant)
        for variant in parsimony_variants
    }
    entries: list[InferenceDisagreementEntry] = []
    for rollup in peptide_rollups:
        if len(rollup.protein_refs) < 2:
            continue
        assignments: dict[str, tuple[str, ...]] = {}
        razor_assignment = razor.get(rollup.canonical_peptide)
        if razor_assignment is not None:
            assignments["razor"] = (razor_assignment.assigned_protein,)
        for variant, selected in parsimony_results.items():
            assignments[f"parsimony:{variant.value}"] = tuple(
                entry.protein_ref
                for entry in selected
                if rollup.canonical_peptide in entry.covered_peptides
            )
        flattened = {
            protein_ref
            for protein_refs in assignments.values()
            for protein_ref in protein_refs
        }
        if len(flattened) > 1:
            entries.append(
                InferenceDisagreementEntry(
                    subject_id=rollup.canonical_peptide,
                    kind=InferenceDisagreementKind.PEPTIDE_ASSIGNMENT,
                    strategy_assignments=assignments,
                    note="shared peptide support diverges across razor and parsimony strategies",
                )
            )

    comparison = compare_parsimony_variants(records, variants=parsimony_variants)
    for difference in comparison.differences:
        if (
            not difference.left_only_proteins
            and not difference.right_only_proteins
            and difference.first_difference_rank is None
        ):
            continue
        entries.append(
            InferenceDisagreementEntry(
                subject_id=f"{difference.left_variant.value}__vs__{difference.right_variant.value}",
                kind=InferenceDisagreementKind.PROTEIN_SET,
                strategy_assignments={
                    difference.left_variant.value: tuple(
                        entry.protein_ref
                        for entry in parsimony_results[difference.left_variant]
                    ),
                    difference.right_variant.value: tuple(
                        entry.protein_ref
                        for entry in parsimony_results[difference.right_variant]
                    ),
                },
                note="named parsimony variants diverge in protein-set membership or ranking over the same evidence",
            )
        )
    return InferenceDisagreementReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.kind.value, entry.subject_id))
        )
    )


def infer_proteins_by_parsimony(
    records: tuple[PsmRecord, ...],
    *,
    variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
) -> tuple[ParsimonyProteinEntry, ...]:
    """Greedily select a parsimonious protein set that explains observed peptides."""
    from bijux_proteomics.identification.protein_parsimony import (
        build_protein_parsimony_report,
    )

    report = build_protein_parsimony_report(
        records,
        variant=variant,
        review_variants=(variant,),
    )
    return tuple(
        ParsimonyProteinEntry(
            variant=entry.variant,
            selection_rank=entry.selection_rank,
            protein_ref=entry.protein_ref,
            source_group_id=entry.source_group_id,
            covered_peptides=entry.covered_peptides,
            newly_explained_peptides=entry.newly_explained_peptides,
            best_score=entry.best_score,
            best_q_value=entry.best_q_value,
            target_decoy_label=entry.target_decoy_label,
        )
        for entry in report.selected_proteins
    )


def compare_parsimony_variants(
    records: tuple[PsmRecord, ...],
    *,
    variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> ParsimonyVariantComparisonReport:
    """Compare multiple named parsimony policies over the same PSM evidence."""
    from bijux_proteomics.identification.protein_parsimony import (
        build_protein_parsimony_report,
    )

    primary_variant = variants[0] if variants else ParsimonyVariant.GREEDY_COVERAGE
    report = build_protein_parsimony_report(
        records,
        variant=primary_variant,
        review_variants=variants,
    )
    return report.variant_comparison

__all__ = [
    'ParsimonyVariant',
    'ParsimonyProteinEntry',
    'InferenceDisagreementKind',
    'InferenceDisagreementEntry',
    'InferenceDisagreementReport',
    'ParsimonyVariantResult',
    'ParsimonyVariantDifferenceEntry',
    'ParsimonyVariantComparisonReport',
    'build_inference_disagreement_report',
    'infer_proteins_by_parsimony',
    'compare_parsimony_variants',
]
