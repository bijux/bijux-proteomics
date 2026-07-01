# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway activity scoring over protein matrices with explicit member coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.interpretation.pathway_activity.knowledge_coverage import (
    pathway_coverage_by_id,
)
from bijux_proteomics.interpretation.pathway_activity.member_resolution import (
    gene_to_protein_refs,
    group_pathway_records,
    protein_gene_annotations,
    protein_refs_in_table,
    standardized_protein_ref_values,
)
from bijux_proteomics.interpretation.pathway_activity.models import (
    PathwayActivityConfidenceStatus,
    PathwayActivityPolicy,
    PathwayActivityReport,
    PathwayActivitySummary,
    PathwayConditionComparisonEntry,
    PathwayConditionScoreEntry,
    PathwayMemberContributionEntry,
    PathwaySampleScoreEntry,
    UnresolvedPathwayActivityMemberEntry,
)
from bijux_proteomics.interpretation.pathway_activity.score_calculation import (
    build_condition_comparisons,
    build_condition_scores,
    build_sample_scores_and_member_contributions,
)
from bijux_proteomics.interpretation.pathway_enrichment import PathwayMembershipRecord
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


def build_pathway_activity_report(
    table: LabelFreeQuantTable,
    pathway_records: tuple[PathwayMembershipRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    fasta_records: tuple[NormalizedProteinRecord, ...] = (),
    custom_annotations: tuple[ProteinAnnotationRecord, ...] = (),
    policy: PathwayActivityPolicy | None = None,
) -> PathwayActivityReport:
    """Score pathway activity per sample over one protein quantification table."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "pathway activity scoring requires a protein-level quantification table"
        )

    active_policy = policy or PathwayActivityPolicy()
    sample_ids = table.sample_ids
    sample_conditions = _condition_lookup(design_entries)
    sample_batches = {entry.sample_id: entry.batch for entry in design_entries}
    pathway_groups = group_pathway_records(pathway_records)
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
    coverage_by_pathway_id = pathway_coverage_by_id(
        available_protein_refs,
        pathway_records,
        policy=active_policy,
    )

    sample_scores, member_contributions, unresolved_members = (
        build_sample_scores_and_member_contributions(
            pathway_groups=pathway_groups,
            sample_ids=sample_ids,
            sample_conditions=sample_conditions,
            sample_batches=sample_batches,
            protein_scores=protein_scores,
            available_protein_refs=available_protein_refs,
            gene_to_proteins=gene_to_proteins,
            minimum_observed_member_count=active_policy.minimum_observed_member_count,
            minimum_knowledge_coverage_fraction=(
                active_policy.minimum_knowledge_coverage_fraction
            ),
            coverage_by_pathway_id=coverage_by_pathway_id,
        )
    )

    condition_scores = build_condition_scores(sample_scores)
    condition_comparisons = build_condition_comparisons(condition_scores)
    return PathwayActivityReport(
        sample_ids=sample_ids,
        sample_scores=tuple(sample_scores),
        condition_scores=tuple(condition_scores),
        condition_comparisons=tuple(condition_comparisons),
        member_contributions=tuple(member_contributions),
        unresolved_members=tuple(unresolved_members),
        summary=PathwayActivitySummary(
            entity_level=table.entity_level,
            measure_kind=table.measure_kind,
            aggregation_method=table.aggregation_method,
            normalization_method=table.normalization_method,
            pathway_count=len(pathway_groups),
            sample_count=len(sample_ids),
            sample_score_count=len(sample_scores),
            scored_sample_count=sum(
                1 for entry in sample_scores if entry.activity_score is not None
            ),
            high_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
            ),
            low_confidence_sample_score_count=sum(
                1
                for entry in sample_scores
                if entry.confidence_status
                is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
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
            "pathway activity scoring computes sample-level pathway scores from the "
            "protein matrix, preserves member coverage and missingness explicitly, and "
            "downgrades sparse pathways to low confidence instead of ignoring coverage"
        ),
    )


__all__ = [
    "PathwayActivityConfidenceStatus",
    "PathwayActivityPolicy",
    "PathwayActivityReport",
    "PathwayActivitySummary",
    "PathwayConditionComparisonEntry",
    "PathwayConditionScoreEntry",
    "PathwayMemberContributionEntry",
    "PathwaySampleScoreEntry",
    "UnresolvedPathwayActivityMemberEntry",
    "build_pathway_activity_report",
]
