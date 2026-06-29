# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway activity scoring over protein matrices with explicit member coverage."""

from __future__ import annotations

from collections import defaultdict
import csv
from io import StringIO
import math
from typing import TYPE_CHECKING

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.domain import ConfidenceTier
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.quantification.contracts.input_models import (
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


PathwayActivityConfidenceStatus = ConfidenceTier


class PathwaySampleScoreEntry(JsonModel):
    """One sample-level activity score for one pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    batch: str | None = None
    activity_score: float | None = None
    total_member_count: int = Field(..., ge=0)
    observed_member_count: int = Field(..., ge=0)
    missing_member_count: int = Field(..., ge=0)
    observed_fraction: float = Field(..., ge=0.0, le=1.0)
    minimum_observed_member_count: int = Field(..., ge=1)
    confidence_status: PathwayActivityConfidenceStatus
    confidence_reason: str | None = None
    observed_member_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class PathwayConditionScoreEntry(JsonModel):
    """One condition-level mean activity score for one pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_count: int = Field(..., ge=0)
    low_confidence_sample_count: int = Field(..., ge=0)
    confidence_status: PathwayActivityConfidenceStatus
    mean_activity_score: float | None = None


class PathwayConditionComparisonEntry(JsonModel):
    """One pairwise condition contrast over one pathway activity profile."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    condition_a_confidence_status: PathwayActivityConfidenceStatus
    condition_b_confidence_status: PathwayActivityConfidenceStatus
    comparison_confidence_status: PathwayActivityConfidenceStatus
    mean_activity_score_a: float | None = None
    mean_activity_score_b: float | None = None
    activity_score_delta: float | None = None


class PathwayMemberContributionEntry(JsonModel):
    """One sample-level member contribution row for one pathway."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    batch: str | None = None
    member_kind: PathwayMemberKind
    member_id: str = Field(..., min_length=1)
    resolved_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    resolved_protein_count: int = Field(..., ge=0)
    observed_protein_count: int = Field(..., ge=0)
    missing_protein_count: int = Field(..., ge=0)
    member_activity_score: float | None = None
    observed: bool


class UnresolvedPathwayActivityMemberEntry(JsonModel):
    """One pathway member that could not be resolved onto the scored study matrix."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind
    member_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class PathwayActivitySummary(JsonModel):
    """Stable summary over one pathway activity scoring run."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    pathway_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    sample_score_count: int = Field(..., ge=0)
    scored_sample_count: int = Field(..., ge=0)
    high_confidence_sample_score_count: int = Field(..., ge=0)
    low_confidence_sample_score_count: int = Field(..., ge=0)
    sample_entries_with_missing_members: int = Field(..., ge=0)
    member_contribution_count: int = Field(..., ge=0)
    unresolved_member_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    condition_comparison_count: int = Field(..., ge=0)


class PathwayActivityPolicy(JsonModel):
    """Confidence policy for pathway activity scoring."""

    model_config = ConfigDict(extra="forbid")

    minimum_observed_member_count: int = Field(default=2, ge=1)
    minimum_knowledge_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


class PathwayActivityReport(JsonModel):
    """Owned pathway activity report over a protein quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_scores: tuple[PathwaySampleScoreEntry, ...] = Field(default_factory=tuple)
    condition_scores: tuple[PathwayConditionScoreEntry, ...] = Field(
        default_factory=tuple
    )
    condition_comparisons: tuple[PathwayConditionComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    member_contributions: tuple[PathwayMemberContributionEntry, ...] = Field(
        default_factory=tuple
    )
    unresolved_members: tuple[UnresolvedPathwayActivityMemberEntry, ...] = Field(
        default_factory=tuple
    )
    summary: PathwayActivitySummary
    note: str = Field(..., min_length=1)


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
    pathway_groups = _group_pathway_records(pathway_records)
    protein_scores = _standardized_protein_ref_values(table)
    available_protein_refs = {
        canonicalize_protein_reference(protein_ref)
        for protein_ref in _protein_refs_in_table(table)
    }
    gene_annotations = _protein_gene_annotations(
        fasta_records=fasta_records,
        custom_annotations=custom_annotations,
    )
    gene_to_proteins = _gene_to_protein_refs(
        available_protein_refs=available_protein_refs,
        gene_annotations=gene_annotations,
    )
    from bijux_proteomics_knowledge.pathways.members import (
        PathwayCoveragePolicy,
        resolve_pathway_members,
    )

    coverage_report = resolve_pathway_members(
        tuple(sorted(available_protein_refs)),
        pathway_records,
        policy=PathwayCoveragePolicy(
            minimum_coverage_fraction=active_policy.minimum_knowledge_coverage_fraction
        ),
    )
    coverage_by_pathway_id = {
        entry.pathway_id: entry for entry in coverage_report.confidence_entries
    }

    unresolved_members: list[UnresolvedPathwayActivityMemberEntry] = []
    member_contributions: list[PathwayMemberContributionEntry] = []
    sample_scores: list[PathwaySampleScoreEntry] = []
    for pathway_id in sorted(pathway_groups):
        records = pathway_groups[pathway_id]
        first = records[0]
        pathway_coverage = coverage_by_pathway_id.get(pathway_id)
        member_specs = _build_member_specs(
            records,
            available_protein_refs=available_protein_refs,
            gene_to_proteins=gene_to_proteins,
            unresolved_members=unresolved_members,
        )
        for sample_id in sample_ids:
            observed_member_ids: list[str] = []
            missing_member_ids: list[str] = []
            member_scores: list[float] = []
            for member_kind, member_id, resolved_protein_refs in member_specs:
                observed_protein_refs = tuple(
                    protein_ref
                    for protein_ref in resolved_protein_refs
                    if protein_scores.get((protein_ref, sample_id)) is not None
                )
                member_activity_score = (
                    round(
                        float(
                            np.mean(
                                [
                                    protein_scores[(protein_ref, sample_id)]
                                    for protein_ref in observed_protein_refs
                                ]
                            )
                        ),
                        6,
                    )
                    if observed_protein_refs
                    else None
                )
                if member_activity_score is None:
                    missing_member_ids.append(_member_label(member_kind, member_id))
                else:
                    observed_member_ids.append(_member_label(member_kind, member_id))
                    member_scores.append(member_activity_score)
                member_contributions.append(
                    PathwayMemberContributionEntry(
                        pathway_id=pathway_id,
                        pathway_name=first.pathway_name,
                        source_name=first.source_name,
                        source_accession=first.source_accession,
                        sample_id=sample_id,
                        condition=sample_conditions.get(sample_id),
                        batch=sample_batches.get(sample_id),
                        member_kind=member_kind,
                        member_id=member_id,
                        resolved_protein_refs=resolved_protein_refs,
                        observed_protein_refs=observed_protein_refs,
                        resolved_protein_count=len(resolved_protein_refs),
                        observed_protein_count=len(observed_protein_refs),
                        missing_protein_count=len(resolved_protein_refs)
                        - len(observed_protein_refs),
                        member_activity_score=member_activity_score,
                        observed=member_activity_score is not None,
                    )
                )
            total_member_count = len(member_specs)
            observed_member_count = len(observed_member_ids)
            sample_scores.append(
                PathwaySampleScoreEntry(
                    pathway_id=pathway_id,
                    pathway_name=first.pathway_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    sample_id=sample_id,
                    condition=sample_conditions.get(sample_id),
                    batch=sample_batches.get(sample_id),
                    activity_score=(
                        round(float(np.mean(member_scores)), 6)
                        if member_scores
                        else None
                    ),
                    total_member_count=total_member_count,
                    observed_member_count=observed_member_count,
                    missing_member_count=total_member_count - observed_member_count,
                    observed_fraction=(
                        observed_member_count / total_member_count
                        if total_member_count > 0
                        else 0.0
                    ),
                    minimum_observed_member_count=active_policy.minimum_observed_member_count,
                    confidence_status=_sample_confidence_status(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=(
                            active_policy.minimum_observed_member_count
                        ),
                        pathway_coverage_status=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.confidence_status.value
                        ),
                    ),
                    confidence_reason=_confidence_reason(
                        observed_member_count=observed_member_count,
                        minimum_observed_member_count=(
                            active_policy.minimum_observed_member_count
                        ),
                        pathway_coverage_status=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.confidence_status.value
                        ),
                        pathway_coverage_fraction=(
                            None
                            if pathway_coverage is None
                            else pathway_coverage.coverage_fraction
                        ),
                        minimum_knowledge_coverage_fraction=(
                            active_policy.minimum_knowledge_coverage_fraction
                        ),
                    ),
                    observed_member_ids=tuple(observed_member_ids),
                    missing_member_ids=tuple(missing_member_ids),
                )
            )

    condition_scores = _build_condition_scores(sample_scores)
    condition_comparisons = _build_condition_comparisons(condition_scores)
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


def render_pathway_activity_summary_tsv(report: PathwayActivityReport) -> str:
    """Render the compact pathway activity summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_level",
            "measure_kind",
            "aggregation_method",
            "normalization_method",
            "pathway_count",
            "sample_count",
            "sample_score_count",
            "scored_sample_count",
            "high_confidence_sample_score_count",
            "low_confidence_sample_score_count",
            "sample_entries_with_missing_members",
            "member_contribution_count",
            "unresolved_member_count",
            "condition_count",
            "condition_comparison_count",
        )
    )
    writer.writerow(
        (
            report.summary.entity_level.value,
            report.summary.measure_kind.value,
            report.summary.aggregation_method.value,
            report.summary.normalization_method.value,
            report.summary.pathway_count,
            report.summary.sample_count,
            report.summary.sample_score_count,
            report.summary.scored_sample_count,
            report.summary.high_confidence_sample_score_count,
            report.summary.low_confidence_sample_score_count,
            report.summary.sample_entries_with_missing_members,
            report.summary.member_contribution_count,
            report.summary.unresolved_member_count,
            report.summary.condition_count,
            report.summary.condition_comparison_count,
        )
    )
    return buffer.getvalue()


def render_pathway_activity_matrix_tsv(report: PathwayActivityReport) -> str:
    """Render one pathway-by-sample activity matrix as TSV."""

    sample_ids = report.sample_ids
    grouped_entries: dict[str, dict[str, PathwaySampleScoreEntry]] = defaultdict(dict)
    metadata_by_pathway: dict[str, PathwaySampleScoreEntry] = {}
    for entry in report.sample_scores:
        grouped_entries[entry.pathway_id][entry.sample_id] = entry
        metadata_by_pathway.setdefault(entry.pathway_id, entry)

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            *sample_ids,
        )
    )
    for pathway_id in sorted(grouped_entries):
        metadata = metadata_by_pathway[pathway_id]
        writer.writerow(
            (
                pathway_id,
                metadata.pathway_name or "",
                metadata.source_name or "",
                metadata.source_accession or "",
                *[
                    ""
                    if grouped_entries[pathway_id][sample_id].activity_score is None
                    else f"{grouped_entries[pathway_id][sample_id].activity_score:g}"
                    for sample_id in sample_ids
                ],
            )
        )
    return buffer.getvalue()


def render_pathway_activity_sample_score_tsv(report: PathwayActivityReport) -> str:
    """Render per-sample pathway activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "sample_id",
            "condition",
            "batch",
            "activity_score",
            "total_member_count",
            "observed_member_count",
            "missing_member_count",
            "observed_fraction",
            "minimum_observed_member_count",
            "confidence_status",
            "confidence_reason",
            "observed_member_ids",
            "missing_member_ids",
        )
    )
    for entry in report.sample_scores:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.sample_id,
                entry.condition or "",
                entry.batch or "",
                "" if entry.activity_score is None else f"{entry.activity_score:g}",
                entry.total_member_count,
                entry.observed_member_count,
                entry.missing_member_count,
                f"{entry.observed_fraction:g}",
                entry.minimum_observed_member_count,
                entry.confidence_status.value,
                entry.confidence_reason or "",
                ";".join(entry.observed_member_ids),
                ";".join(entry.missing_member_ids),
            )
        )
    return buffer.getvalue()


def render_pathway_activity_condition_score_tsv(report: PathwayActivityReport) -> str:
    """Render condition-level mean pathway activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "condition",
            "sample_count",
            "scored_sample_count",
            "high_confidence_sample_count",
            "low_confidence_sample_count",
            "confidence_status",
            "mean_activity_score",
        )
    )
    for entry in report.condition_scores:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.condition,
                entry.sample_count,
                entry.scored_sample_count,
                entry.high_confidence_sample_count,
                entry.low_confidence_sample_count,
                entry.confidence_status.value,
                ""
                if entry.mean_activity_score is None
                else f"{entry.mean_activity_score:g}",
            )
        )
    return buffer.getvalue()


def render_pathway_activity_condition_comparison_tsv(
    report: PathwayActivityReport,
) -> str:
    """Render pairwise condition pathway activity contrasts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "condition_a",
            "condition_b",
            "condition_a_confidence_status",
            "condition_b_confidence_status",
            "comparison_confidence_status",
            "mean_activity_score_a",
            "mean_activity_score_b",
            "activity_score_delta",
        )
    )
    for entry in report.condition_comparisons:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.condition_a,
                entry.condition_b,
                entry.condition_a_confidence_status.value,
                entry.condition_b_confidence_status.value,
                entry.comparison_confidence_status.value,
                ""
                if entry.mean_activity_score_a is None
                else f"{entry.mean_activity_score_a:g}",
                ""
                if entry.mean_activity_score_b is None
                else f"{entry.mean_activity_score_b:g}",
                ""
                if entry.activity_score_delta is None
                else f"{entry.activity_score_delta:g}",
            )
        )
    return buffer.getvalue()


def render_pathway_member_contribution_tsv(report: PathwayActivityReport) -> str:
    """Render sample-level pathway member contribution rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "sample_id",
            "condition",
            "batch",
            "member_kind",
            "member_id",
            "resolved_protein_refs",
            "observed_protein_refs",
            "resolved_protein_count",
            "observed_protein_count",
            "missing_protein_count",
            "member_activity_score",
            "observed",
        )
    )
    for entry in report.member_contributions:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.sample_id,
                entry.condition or "",
                entry.batch or "",
                entry.member_kind.value,
                entry.member_id,
                ";".join(entry.resolved_protein_refs),
                ";".join(entry.observed_protein_refs),
                entry.resolved_protein_count,
                entry.observed_protein_count,
                entry.missing_protein_count,
                ""
                if entry.member_activity_score is None
                else f"{entry.member_activity_score:g}",
                str(entry.observed).lower(),
            )
        )
    return buffer.getvalue()


def render_pathway_activity_unresolved_member_tsv(report: PathwayActivityReport) -> str:
    """Render unresolved pathway members as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "member_id",
            "reason",
        )
    )
    for entry in report.unresolved_members:
        writer.writerow(
            (
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.member_kind.value,
                entry.member_id,
                entry.reason,
            )
        )
    return buffer.getvalue()


def _group_pathway_records(
    pathway_records: tuple[PathwayMembershipRecord, ...],
) -> dict[str, list[PathwayMembershipRecord]]:
    grouped: dict[str, list[PathwayMembershipRecord]] = {}
    for record in pathway_records:
        grouped.setdefault(record.pathway_id, []).append(record)
    return grouped


def _protein_refs_in_table(table: LabelFreeQuantTable) -> tuple[str, ...]:
    protein_refs: list[str] = []
    for entity_id in table.entity_ids:
        protein_refs.extend(
            table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        )
    return tuple(
        dict.fromkeys(canonicalize_protein_reference(ref) for ref in protein_refs)
    )


def _standardized_protein_ref_values(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], float | None]:
    value_lookup = _matrix_value_index(table)
    entity_standardized: dict[tuple[str, str], float | None] = {}
    for entity_id in table.entity_ids:
        observed_values: list[float] = []
        sample_values: dict[str, float | None] = {}
        for sample_id in table.sample_ids:
            abundance = value_lookup[(entity_id, sample_id)].abundance
            if abundance is None:
                sample_values[sample_id] = None
                continue
            log_value = math.log2(float(abundance) + 1.0)
            sample_values[sample_id] = log_value
            observed_values.append(log_value)
        if not observed_values:
            for sample_id in table.sample_ids:
                entity_standardized[(entity_id, sample_id)] = None
            continue
        mean_value = float(np.mean(observed_values))
        std_value = float(np.std(observed_values))
        for sample_id in table.sample_ids:
            value = sample_values[sample_id]
            if value is None:
                entity_standardized[(entity_id, sample_id)] = None
            elif std_value <= 1e-12:
                entity_standardized[(entity_id, sample_id)] = 0.0
            else:
                entity_standardized[(entity_id, sample_id)] = (
                    value - mean_value
                ) / std_value

    protein_ref_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for entity_id in table.entity_ids:
        protein_refs = table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        for protein_ref in protein_refs:
            canonical_ref = canonicalize_protein_reference(protein_ref)
            for sample_id in table.sample_ids:
                value = entity_standardized[(entity_id, sample_id)]
                if value is not None:
                    protein_ref_values[(canonical_ref, sample_id)].append(value)

    aggregated: dict[tuple[str, str], float | None] = {}
    for protein_ref in _protein_refs_in_table(table):
        for sample_id in table.sample_ids:
            values = protein_ref_values.get((protein_ref, sample_id), [])
            aggregated[(protein_ref, sample_id)] = (
                round(float(np.mean(values)), 6) if values else None
            )
    return aggregated


def _protein_gene_annotations(
    *,
    fasta_records: tuple[NormalizedProteinRecord, ...],
    custom_annotations: tuple[ProteinAnnotationRecord, ...],
) -> dict[str, tuple[str, ...]]:
    annotations: dict[str, set[str]] = {}
    for fasta_record in fasta_records:
        if fasta_record.gene:
            annotations.setdefault(fasta_record.canonical_accession, set()).add(
                fasta_record.gene
            )
    for annotation_record in custom_annotations:
        if annotation_record.gene_symbol:
            annotations.setdefault(annotation_record.protein_ref, set()).add(
                annotation_record.gene_symbol
            )
    return {
        canonicalize_protein_reference(protein_ref): tuple(sorted(gene_symbols))
        for protein_ref, gene_symbols in annotations.items()
    }


def _gene_to_protein_refs(
    *,
    available_protein_refs: set[str],
    gene_annotations: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    gene_to_proteins: dict[str, set[str]] = {}
    for protein_ref in sorted(available_protein_refs):
        for gene_symbol in gene_annotations.get(protein_ref, ()):
            gene_to_proteins.setdefault(gene_symbol, set()).add(protein_ref)
    return {
        gene_symbol: tuple(sorted(protein_refs))
        for gene_symbol, protein_refs in gene_to_proteins.items()
    }


def _build_member_specs(
    records: list[PathwayMembershipRecord],
    *,
    available_protein_refs: set[str],
    gene_to_proteins: dict[str, tuple[str, ...]],
    unresolved_members: list[UnresolvedPathwayActivityMemberEntry],
) -> tuple[tuple[PathwayMemberKind, str, tuple[str, ...]], ...]:
    first = records[0]
    member_specs: list[tuple[PathwayMemberKind, str, tuple[str, ...]]] = []
    seen_members: set[tuple[str, str]] = set()
    for record in records:
        member_key = (record.member_kind.value, record.member_id)
        if member_key in seen_members:
            continue
        seen_members.add(member_key)
        resolved_protein_refs: tuple[str, ...]
        if record.member_kind is PathwayMemberKind.PROTEIN:
            canonical_ref = canonicalize_protein_reference(record.member_id)
            resolved_protein_refs = (
                (canonical_ref,) if canonical_ref in available_protein_refs else ()
            )
        else:
            resolved_protein_refs = gene_to_proteins.get(record.member_id, ())
        if not resolved_protein_refs:
            unresolved_members.append(
                UnresolvedPathwayActivityMemberEntry(
                    pathway_id=record.pathway_id,
                    pathway_name=first.pathway_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    member_kind=record.member_kind,
                    member_id=record.member_id,
                    reason=(
                        "pathway protein member was not present in the quantification table"
                        if record.member_kind is PathwayMemberKind.PROTEIN
                        else "pathway gene member could not be resolved onto observed proteins"
                    ),
                )
            )
        member_specs.append(
            (record.member_kind, record.member_id, tuple(sorted(resolved_protein_refs)))
        )
    return tuple(member_specs)


def _sample_confidence_status(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
    pathway_coverage_status: str | None,
) -> PathwayActivityConfidenceStatus:
    if observed_member_count < minimum_observed_member_count:
        return PathwayActivityConfidenceStatus.LOW_CONFIDENCE
    if pathway_coverage_status == "low_confidence":
        return PathwayActivityConfidenceStatus.LOW_CONFIDENCE
    return PathwayActivityConfidenceStatus.HIGH_CONFIDENCE


def _aggregate_confidence_status(
    statuses: tuple[PathwayActivityConfidenceStatus, ...],
) -> PathwayActivityConfidenceStatus:
    if all(
        status is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE for status in statuses
    ):
        return PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
    return PathwayActivityConfidenceStatus.LOW_CONFIDENCE


def _confidence_reason(
    *,
    observed_member_count: int,
    minimum_observed_member_count: int,
    pathway_coverage_status: str | None,
    pathway_coverage_fraction: float | None,
    minimum_knowledge_coverage_fraction: float,
) -> str | None:
    reasons: list[str] = []
    if observed_member_count < minimum_observed_member_count:
        reasons.append(
            "observed member count "
            f"{observed_member_count} was below minimum {minimum_observed_member_count}"
        )
    if pathway_coverage_status == "low_confidence":
        if pathway_coverage_fraction is None:
            raise RuntimeError(
                "low-confidence pathway coverage reasoning requires an explicit coverage fraction"
            )
        reasons.append(
            "pathway knowledge coverage "
            f"{pathway_coverage_fraction:g} was below minimum "
            f"{minimum_knowledge_coverage_fraction:g}"
        )
    if not reasons:
        return None
    return "; ".join(reasons)


def _build_condition_scores(
    sample_scores: list[PathwaySampleScoreEntry],
) -> list[PathwayConditionScoreEntry]:
    grouped: dict[tuple[str, str], list[PathwaySampleScoreEntry]] = defaultdict(list)
    for entry in sample_scores:
        if entry.condition is None:
            continue
        grouped[(entry.pathway_id, entry.condition)].append(entry)
    results: list[PathwayConditionScoreEntry] = []
    for (pathway_id, condition), entries in sorted(grouped.items()):
        first = entries[0]
        scored_values = [
            entry.activity_score
            for entry in entries
            if entry.activity_score is not None
        ]
        results.append(
            PathwayConditionScoreEntry(
                pathway_id=pathway_id,
                pathway_name=first.pathway_name,
                source_name=first.source_name,
                source_accession=first.source_accession,
                condition=condition,
                sample_count=len(entries),
                scored_sample_count=len(scored_values),
                high_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
                ),
                low_confidence_sample_count=sum(
                    1
                    for entry in entries
                    if entry.confidence_status
                    is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
                ),
                confidence_status=_aggregate_confidence_status(
                    tuple(entry.confidence_status for entry in entries)
                ),
                mean_activity_score=(
                    round(float(np.mean(scored_values)), 6) if scored_values else None
                ),
            )
        )
    return results


def _build_condition_comparisons(
    condition_scores: list[PathwayConditionScoreEntry],
) -> list[PathwayConditionComparisonEntry]:
    grouped: dict[str, list[PathwayConditionScoreEntry]] = defaultdict(list)
    for entry in condition_scores:
        grouped[entry.pathway_id].append(entry)
    results: list[PathwayConditionComparisonEntry] = []
    for pathway_id in sorted(grouped):
        entries = sorted(grouped[pathway_id], key=lambda entry: entry.condition)
        for left_index in range(len(entries)):
            for right_index in range(left_index + 1, len(entries)):
                left = entries[left_index]
                right = entries[right_index]
                delta = (
                    round(right.mean_activity_score - left.mean_activity_score, 6)
                    if left.mean_activity_score is not None
                    and right.mean_activity_score is not None
                    else None
                )
                results.append(
                    PathwayConditionComparisonEntry(
                        pathway_id=pathway_id,
                        pathway_name=left.pathway_name,
                        source_name=left.source_name,
                        source_accession=left.source_accession,
                        condition_a=left.condition,
                        condition_b=right.condition,
                        condition_a_confidence_status=left.confidence_status,
                        condition_b_confidence_status=right.confidence_status,
                        comparison_confidence_status=_aggregate_confidence_status(
                            (left.confidence_status, right.confidence_status)
                        ),
                        mean_activity_score_a=left.mean_activity_score,
                        mean_activity_score_b=right.mean_activity_score,
                        activity_score_delta=delta,
                    )
                )
    return results


def _member_label(member_kind: PathwayMemberKind, member_id: str) -> str:
    return f"{member_kind.value}:{member_id}"


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
    "render_pathway_activity_condition_comparison_tsv",
    "render_pathway_activity_condition_score_tsv",
    "render_pathway_activity_matrix_tsv",
    "render_pathway_activity_sample_score_tsv",
    "render_pathway_activity_summary_tsv",
    "render_pathway_activity_unresolved_member_tsv",
    "render_pathway_member_contribution_tsv",
]
