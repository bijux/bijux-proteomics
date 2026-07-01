# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein complex activity scoring over protein matrices with limiting subunits."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.complex_activity.member_resolution import (
    gene_to_protein_refs,
    group_complex_records,
    protein_gene_annotations,
    protein_refs_in_table,
    standardized_protein_ref_values,
)
from bijux_proteomics.interpretation.complex_activity.models import (
    ComplexActivityConfidenceStatus,
    ComplexActivityPolicy,
    ComplexActivityReport,
    ComplexActivitySummary,
    ComplexConditionComparisonEntry,
    ComplexConditionScoreEntry,
    ComplexMemberContributionEntry,
    ComplexSampleScoreEntry,
    UnresolvedComplexActivityMemberEntry,
)
from bijux_proteomics.interpretation.complex_activity.score_calculation import (
    build_condition_comparisons,
    build_condition_scores,
    build_sample_scores_and_member_contributions,
)
from bijux_proteomics.interpretation.complex_enrichment import ComplexMembershipRecord
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.quantification.contracts.input_models import (
    QuantEntityLevel,
)
from bijux_proteomics.quantification.contracts.matrix_building import _condition_lookup
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.sequences.core import NormalizedProteinRecord

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


def build_complex_activity_report(
    table: LabelFreeQuantTable,
    complex_records: tuple[ComplexMembershipRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    fasta_records: tuple[NormalizedProteinRecord, ...] = (),
    custom_annotations: tuple[ProteinAnnotationRecord, ...] = (),
    policy: ComplexActivityPolicy | None = None,
) -> ComplexActivityReport:
    """Score complex activity per sample over one protein quantification table."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "complex activity scoring requires a protein-level quantification table"
        )

    active_policy = policy or ComplexActivityPolicy()
    sample_ids = table.sample_ids
    sample_conditions = _condition_lookup(design_entries)
    sample_batches = {entry.sample_id: entry.batch for entry in design_entries}
    complex_groups = group_complex_records(complex_records)
    protein_scores = standardized_protein_ref_values(table)
    available_protein_refs = set(protein_refs_in_table(table))
    gene_annotations = protein_gene_annotations(
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
    )
    gene_to_proteins = gene_to_protein_refs(
        available_protein_refs=available_protein_refs,
        gene_annotations=gene_annotations,
    )

    sample_scores, member_contributions, unresolved_members = (
        build_sample_scores_and_member_contributions(
            complex_groups=complex_groups,
            sample_ids=sample_ids,
            sample_conditions=sample_conditions,
            sample_batches=sample_batches,
            protein_scores=protein_scores,
            available_protein_refs=available_protein_refs,
            gene_to_proteins=gene_to_proteins,
            minimum_observed_member_count=active_policy.minimum_observed_member_count,
        )
    )
    condition_scores = build_condition_scores(sample_scores, member_contributions)
    condition_comparisons = build_condition_comparisons(condition_scores)
    return ComplexActivityReport(
        sample_ids=sample_ids,
        sample_scores=tuple(sample_scores),
        condition_scores=tuple(condition_scores),
        condition_comparisons=tuple(condition_comparisons),
        member_contributions=tuple(member_contributions),
        unresolved_members=tuple(unresolved_members),
        summary=ComplexActivitySummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method,
            complex_count=len(complex_groups),
            sample_count=len(sample_ids),
            sample_score_count=len(sample_scores),
            scored_sample_count=sum(
                1 for entry in sample_scores if entry.activity_score is not None
            ),
            high_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ComplexActivityConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
            ),
            sample_entries_with_missing_members=sum(
                1 for entry in sample_scores if entry.missing_member_count > 0
            ),
            member_contribution_count=len(member_contributions),
            unresolved_member_count=len(unresolved_members),
            condition_count=len({entry.condition for entry in condition_scores}),
            condition_comparison_count=len(condition_comparisons),
        ),
        note=(
            "complex activity scoring computes sample-level complex scores from the "
            "protein matrix, preserves observed and missing members, reports limiting "
            "subunits explicitly, and downgrades sparse complexes to low confidence"
        ),
    )


__all__ = [
    "ComplexActivityConfidenceStatus",
    "ComplexActivityPolicy",
    "ComplexActivityReport",
    "ComplexActivitySummary",
    "ComplexConditionComparisonEntry",
    "ComplexConditionScoreEntry",
    "ComplexMemberContributionEntry",
    "ComplexSampleScoreEntry",
    "UnresolvedComplexActivityMemberEntry",
    "build_complex_activity_report",
]
