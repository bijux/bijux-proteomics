# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compartment-level biology review over explicit subcellular context mappings."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
)
from bijux_proteomics.interpretation.protein_set_enrichment import (
    ProteinSetEnrichmentBackgroundSource,
    ProteinSetEnrichmentEntry,
    ProteinSetEnrichmentPolicy,
    ProteinSetEnrichmentReport,
    ProteinSetEnrichmentSummary,
    build_protein_set_enrichment_report,
)
from bijux_proteomics.interpretation.protein_set_scoring import (
    ProteinSetRecord,
    ProteinSetSampleScoreEntry,
    ProteinSetScoringPolicy,
    ProteinSetScoringReport,
    build_protein_set_scoring_report,
)
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
)
from bijux_proteomics.quantification.contracts.input_models import QuantEntityLevel
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.formats import ExperimentalDesignEntry


class CompartmentLocalizationScope(StrEnum):
    """Whether an unknown-localization protein came from the foreground or background."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"


class CompartmentBiologyPolicy(JsonModel):
    """Selection and confidence policy for compartment-level biology review."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    min_enrichment_ratio: float = Field(default=1.0, ge=0.0)
    minimum_observed_member_count: int = Field(default=2, ge=1)


class CompartmentUnknownLocalizationEntry(JsonModel):
    """One protein that remained outside explicit compartment annotations."""

    model_config = ConfigDict(extra="forbid")

    localization_scope: CompartmentLocalizationScope
    protein_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class CompartmentBiologySummary(JsonModel):
    """Stable summary over one compartment biology pass."""

    model_config = ConfigDict(extra="forbid")

    compartment_count: int = Field(..., ge=0)
    foreground_protein_count: int = Field(..., ge=0)
    background_protein_count: int = Field(..., ge=0)
    evaluated_compartment_count: int = Field(..., ge=0)
    enriched_compartment_count: int = Field(..., ge=0)
    unknown_foreground_protein_count: int = Field(..., ge=0)
    unknown_background_protein_count: int = Field(..., ge=0)
    low_confidence_sample_score_count: int = Field(..., ge=0)
    unresolved_member_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    condition_comparison_count: int = Field(..., ge=0)


class CompartmentBiologyReport(JsonModel):
    """Owned compartment biology report over changed proteins and measured background."""

    model_config = ConfigDict(extra="forbid")

    policy: CompartmentBiologyPolicy
    enrichment_report: ProteinSetEnrichmentReport
    activity_report: ProteinSetScoringReport
    unknown_localization_entries: tuple[CompartmentUnknownLocalizationEntry, ...] = (
        Field(default_factory=tuple)
    )
    summary: CompartmentBiologySummary
    note: str = Field(..., min_length=1)


def build_compartment_biology_report(
    table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    context_records: tuple[BiologicalContextRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    policy: CompartmentBiologyPolicy | None = None,
) -> CompartmentBiologyReport:
    """Interpret changed proteins through explicit subcellular compartment context."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "compartment biology requires a protein-level quantification table"
        )

    active_policy = policy or CompartmentBiologyPolicy()
    compartment_records = tuple(
        record
        for record in context_records
        if record.context_kind is BiologicalContextKind.SUBCELLULAR_COMPARTMENT
    )
    if not compartment_records:
        raise ValueError(
            "compartment biology requires at least one subcellular_compartment context record"
        )

    compartment_set_records = _build_compartment_set_records(compartment_records)
    background_entries = _build_background_protein_entries(table)
    if not background_entries:
        raise ValueError(
            "compartment biology requires entity_protein_refs on the protein quantification table"
        )
    foreground_entries = _build_foreground_protein_entries(
        differential_report,
        protein_refs_by_entity=table.entity_protein_refs,
        policy=active_policy,
    )
    enrichment_report = (
        _build_empty_compartment_enrichment_report(
            foreground_size=0,
            background_size=len(background_entries),
        )
        if not foreground_entries
        else build_protein_set_enrichment_report(
            foreground_entries,
            compartment_set_records,
            background_entries=background_entries,
            policy=ProteinSetEnrichmentPolicy(
                max_adjusted_p_value=1.0,
                min_enrichment_ratio=0.0,
            ),
        )
    )
    activity_report = build_protein_set_scoring_report(
        table,
        compartment_set_records,
        design_entries=design_entries,
        policy=ProteinSetScoringPolicy(
            minimum_observed_member_count=active_policy.minimum_observed_member_count
        ),
    )
    unknown_localization_entries = _build_unknown_localization_entries(
        background_entries=background_entries,
        foreground_entries=foreground_entries,
        compartment_set_records=compartment_set_records,
    )
    return CompartmentBiologyReport(
        policy=active_policy,
        enrichment_report=enrichment_report,
        activity_report=activity_report,
        unknown_localization_entries=unknown_localization_entries,
        summary=CompartmentBiologySummary(
            compartment_count=len(
                {record.set_id for record in compartment_set_records}
            ),
            foreground_protein_count=len(foreground_entries),
            background_protein_count=len(background_entries),
            evaluated_compartment_count=enrichment_report.summary.evaluated_set_count,
            enriched_compartment_count=sum(
                1
                for entry in enrichment_report.entries
                if _passes_enrichment_filter(entry, active_policy)
            ),
            unknown_foreground_protein_count=sum(
                1
                for entry in unknown_localization_entries
                if entry.localization_scope is CompartmentLocalizationScope.FOREGROUND
            ),
            unknown_background_protein_count=sum(
                1
                for entry in unknown_localization_entries
                if entry.localization_scope is CompartmentLocalizationScope.BACKGROUND
            ),
            low_confidence_sample_score_count=(
                activity_report.summary.low_confidence_sample_score_count
            ),
            unresolved_member_count=activity_report.summary.unresolved_member_count,
            condition_count=activity_report.summary.condition_count,
            condition_comparison_count=activity_report.summary.condition_comparison_count,
        ),
        note=(
            "compartment biology interprets changed proteins through explicit "
            "subcellular localization records, preserves enrichment support and "
            "sample-level compartment activity, and keeps proteins without "
            "compartment evidence reviewable instead of dropping them silently"
        ),
    )


def render_compartment_biology_summary_tsv(report: CompartmentBiologyReport) -> str:
    """Render the compact compartment biology summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_count",
            "foreground_protein_count",
            "background_protein_count",
            "evaluated_compartment_count",
            "enriched_compartment_count",
            "unknown_foreground_protein_count",
            "unknown_background_protein_count",
            "low_confidence_sample_score_count",
            "unresolved_member_count",
            "condition_count",
            "condition_comparison_count",
        )
    )
    writer.writerow(
        (
            report.summary.compartment_count,
            report.summary.foreground_protein_count,
            report.summary.background_protein_count,
            report.summary.evaluated_compartment_count,
            report.summary.enriched_compartment_count,
            report.summary.unknown_foreground_protein_count,
            report.summary.unknown_background_protein_count,
            report.summary.low_confidence_sample_score_count,
            report.summary.unresolved_member_count,
            report.summary.condition_count,
            report.summary.condition_comparison_count,
        )
    )
    return buffer.getvalue()


def render_compartment_enrichment_tsv(report: CompartmentBiologyReport) -> str:
    """Render compartment enrichment rows with explicit support and filter status."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
            "source_name",
            "source_accession",
            "foreground_overlap_count",
            "background_member_count",
            "foreground_size",
            "background_size",
            "expected_overlap_count",
            "enrichment_ratio",
            "p_value",
            "adjusted_p_value",
            "passes_enrichment_filter",
            "supporting_protein_refs",
        )
    )
    for entry in report.enrichment_report.entries:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.foreground_overlap_count,
                entry.background_member_count,
                entry.foreground_size,
                entry.background_size,
                f"{entry.expected_overlap_count:g}",
                "" if entry.enrichment_ratio is None else f"{entry.enrichment_ratio:g}",
                f"{entry.p_value:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                str(_passes_enrichment_filter(entry, report.policy)).lower(),
                ";".join(entry.supporting_protein_refs),
            )
        )
    return buffer.getvalue()


def render_compartment_activity_matrix_tsv(report: CompartmentBiologyReport) -> str:
    """Render one compartment-by-sample activity matrix as TSV."""

    sample_ids = report.activity_report.sample_ids
    grouped_entries: dict[str, dict[str, ProteinSetSampleScoreEntry]] = {}
    metadata_by_compartment: dict[str, ProteinSetSampleScoreEntry] = {}
    for entry in report.activity_report.sample_scores:
        grouped_entries.setdefault(entry.set_id, {})[entry.sample_id] = entry
        metadata_by_compartment.setdefault(entry.set_id, entry)

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
            "source_name",
            "source_accession",
            *sample_ids,
        )
    )
    for compartment_id in sorted(grouped_entries):
        metadata = metadata_by_compartment[compartment_id]
        writer.writerow(
            (
                compartment_id,
                metadata.set_name or "",
                metadata.source_name or "",
                metadata.source_accession or "",
                *[
                    ""
                    if grouped_entries[compartment_id][sample_id].activity_score is None
                    else f"{grouped_entries[compartment_id][sample_id].activity_score:g}"
                    for sample_id in sample_ids
                ],
            )
        )
    return buffer.getvalue()


def render_compartment_activity_sample_score_tsv(
    report: CompartmentBiologyReport,
) -> str:
    """Render per-sample compartment activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
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
    for entry in report.activity_report.sample_scores:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
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


def render_compartment_activity_condition_score_tsv(
    report: CompartmentBiologyReport,
) -> str:
    """Render condition-level mean compartment activity scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
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
    for entry in report.activity_report.condition_scores:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
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


def render_compartment_activity_condition_comparison_tsv(
    report: CompartmentBiologyReport,
) -> str:
    """Render pairwise condition compartment activity contrasts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
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
    for entry in report.activity_report.condition_comparisons:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
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


def render_compartment_activity_unresolved_member_tsv(
    report: CompartmentBiologyReport,
) -> str:
    """Render compartment members that could not be resolved onto the study matrix."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "compartment_id",
            "compartment_name",
            "source_name",
            "source_accession",
            "protein_ref",
            "reason",
        )
    )
    for entry in report.activity_report.unresolved_members:
        writer.writerow(
            (
                entry.set_id,
                entry.set_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.protein_ref,
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_unknown_compartment_localization_tsv(
    report: CompartmentBiologyReport,
) -> str:
    """Render proteins that lacked explicit compartment annotations as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "localization_scope",
            "protein_ref",
            "reason",
        )
    )
    for entry in report.unknown_localization_entries:
        writer.writerow(
            (
                entry.localization_scope.value,
                entry.protein_ref,
                entry.reason,
            )
        )
    return buffer.getvalue()


def _build_compartment_set_records(
    context_records: tuple[BiologicalContextRecord, ...],
) -> tuple[ProteinSetRecord, ...]:
    records: list[ProteinSetRecord] = []
    seen_memberships: set[tuple[str, str, str | None, str | None]] = set()
    for record in sorted(
        context_records,
        key=lambda entry: (
            entry.context_id,
            entry.protein_ref,
            entry.source_name or "",
            entry.source_accession or "",
        ),
    ):
        membership_key = (
            record.context_id,
            record.protein_ref,
            record.source_name,
            record.source_accession,
        )
        if membership_key in seen_memberships:
            continue
        seen_memberships.add(membership_key)
        records.append(
            ProteinSetRecord(
                set_id=record.context_id,
                protein_ref=record.protein_ref,
                set_name=record.context_name,
                set_category=BiologicalContextKind.SUBCELLULAR_COMPARTMENT.value,
                source_name=record.source_name,
                source_accession=record.source_accession,
                metadata=record.metadata,
            )
        )
    return tuple(records)


def _build_background_protein_entries(
    table: LabelFreeQuantTable,
) -> tuple[ProteinReferenceEntry, ...]:
    seen: set[str] = set()
    entries: list[ProteinReferenceEntry] = []
    for protein_ref in sorted(
        {
            canonicalize_protein_reference(protein_ref)
            for protein_refs in table.entity_protein_refs.values()
            for protein_ref in protein_refs
        }
    ):
        if protein_ref in seen:
            continue
        seen.add(protein_ref)
        entries.append(
            ProteinReferenceEntry(
                row_number=len(entries) + 2,
                source_row_id=f"background:{protein_ref}",
                input_protein_ref=protein_ref,
                protein_ref=protein_ref,
            )
        )
    return tuple(entries)


def _build_foreground_protein_entries(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]],
    policy: CompartmentBiologyPolicy,
) -> tuple[ProteinReferenceEntry, ...]:
    seen: set[str] = set()
    entries: list[ProteinReferenceEntry] = []
    for differential_entry in sorted(
        differential_report.entries,
        key=lambda entry: (
            entry.adjusted_p_value if entry.adjusted_p_value is not None else 1.0,
            -abs(entry.log2_fold_change),
            entry.entity_id,
        ),
    ):
        if differential_entry.adjusted_p_value is None:
            continue
        if differential_entry.adjusted_p_value > policy.max_adjusted_p_value:
            continue
        if (
            abs(differential_entry.log2_fold_change)
            < policy.min_absolute_log2_fold_change
        ):
            continue
        for protein_ref in protein_refs_by_entity.get(differential_entry.entity_id, ()):
            normalized_ref = canonicalize_protein_reference(protein_ref)
            if normalized_ref in seen:
                continue
            seen.add(normalized_ref)
            entries.append(
                ProteinReferenceEntry(
                    row_number=len(entries) + 2,
                    source_row_id=differential_entry.entity_id,
                    input_protein_ref=protein_ref,
                    protein_ref=normalized_ref,
                )
            )
    return tuple(entries)


def _build_unknown_localization_entries(
    *,
    background_entries: tuple[ProteinReferenceEntry, ...],
    foreground_entries: tuple[ProteinReferenceEntry, ...],
    compartment_set_records: tuple[ProteinSetRecord, ...],
) -> tuple[CompartmentUnknownLocalizationEntry, ...]:
    compartment_protein_refs = {
        record.protein_ref for record in compartment_set_records
    }
    unknown_entries: list[CompartmentUnknownLocalizationEntry] = []
    for scope, entries in (
        (CompartmentLocalizationScope.FOREGROUND, foreground_entries),
        (CompartmentLocalizationScope.BACKGROUND, background_entries),
    ):
        for entry in entries:
            if entry.protein_ref in compartment_protein_refs:
                continue
            unknown_entries.append(
                CompartmentUnknownLocalizationEntry(
                    localization_scope=scope,
                    protein_ref=entry.protein_ref,
                    reason=(
                        "protein had no user-supplied subcellular compartment annotation"
                    ),
                )
            )
    return tuple(
        sorted(
            unknown_entries,
            key=lambda entry: (entry.localization_scope.value, entry.protein_ref),
        )
    )


def _build_empty_compartment_enrichment_report(
    *,
    foreground_size: int,
    background_size: int,
) -> ProteinSetEnrichmentReport:
    return ProteinSetEnrichmentReport(
        entries=(),
        universe_gap_entries=(),
        summary=ProteinSetEnrichmentSummary(
            foreground_size=foreground_size,
            background_size=background_size,
            background_source=ProteinSetEnrichmentBackgroundSource.EXPLICIT_INPUT,
            evaluated_set_count=0,
            enriched_set_count=0,
            category_counts={},
            foreground_universe_gap_count=0,
            background_universe_gap_count=0,
        ),
        note=(
            "compartment enrichment preserved the explicit measured background, but no "
            "proteins passed the foreground selection policy for this contrast"
        ),
    )


def _passes_enrichment_filter(
    entry: ProteinSetEnrichmentEntry,
    policy: CompartmentBiologyPolicy,
) -> bool:
    if entry.adjusted_p_value is None:
        return False
    if entry.adjusted_p_value > policy.max_adjusted_p_value:
        return False
    if entry.enrichment_ratio is None:
        return False
    return entry.enrichment_ratio >= policy.min_enrichment_ratio
