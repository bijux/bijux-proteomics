# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study pathway comparison over owned biological study results."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
import re
from statistics import mean

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    PathwayActivityConfidenceStatus,
    PathwayActivityReport,
    PathwayEnrichmentCorrectionPolicy,
    PathwayMemberKind,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinStudyInput,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind
from bijux_proteomics_foundation import JsonModel


class CrossStudyPathwaySignalKind(StrEnum):
    """Comparable cross-study pathway signal families."""

    ACTIVITY = "activity"
    ENRICHMENT = "enrichment"


class CrossStudyPathwayDirection(StrEnum):
    """Stable pathway signal directions."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class CrossStudyPathwayComparisonStatus(StrEnum):
    """Stable pathway-comparison outcomes across studies."""

    SHARED_SIGNAL = "shared_signal"
    OPPOSITE_SIGNAL = "opposite_signal"
    STUDY_SPECIFIC_SIGNAL = "study_specific_signal"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    INSUFFICIENT_SUPPORT = "insufficient_support"


class CrossStudyPathwayContrastAlignmentStatus(StrEnum):
    """Whether activity contrasts aligned cleanly across studies."""

    SAME_ORDERED_CONTRAST = "same_ordered_contrast"
    REVERSED_ORDER_NORMALIZED = "reversed_order_normalized"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    NOT_APPLICABLE = "not_applicable"


class CrossStudyPathwayObservation(JsonModel):
    """One study-level pathway signal that can be compared across studies."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    signal_kind: CrossStudyPathwaySignalKind
    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind | None = None
    condition_a: str | None = None
    condition_b: str | None = None
    direction: CrossStudyPathwayDirection | None = None
    activity_score_delta: float | None = None
    activity_confidence_status: PathwayActivityConfidenceStatus | None = None
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    significant: bool = False
    total_member_count: int | None = Field(default=None, ge=0)
    foreground_overlap_count: int | None = Field(default=None, ge=0)
    background_member_count: int | None = Field(default=None, ge=0)
    condition_a_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    condition_b_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class CrossStudyPathwayUnsupportedStudy(JsonModel):
    """One study result that could not contribute comparable pathway signals."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    reason: str = Field(..., min_length=1)


class CrossStudyPathwayExtractionSummary(JsonModel):
    """Summary over extracted cross-study pathway signals."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    activity_observation_count: int = Field(..., ge=0)
    enrichment_observation_count: int = Field(..., ge=0)


class CrossStudyPathwayExtractionReport(JsonModel):
    """Owned extraction report over study pathway signals."""

    model_config = ConfigDict(extra="forbid")

    observations: tuple[CrossStudyPathwayObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[CrossStudyPathwayUnsupportedStudy, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyPathwayExtractionSummary
    note: str = Field(..., min_length=1)


class CrossStudyPathwayStudyEntry(JsonModel):
    """One study-specific signal aligned under one pathway comparison group."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., min_length=1)
    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    signal_kind: CrossStudyPathwaySignalKind
    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind | None = None
    condition_a: str | None = None
    condition_b: str | None = None
    direction: CrossStudyPathwayDirection | None = None
    normalized_direction: CrossStudyPathwayDirection | None = None
    activity_score_delta: float | None = None
    normalized_activity_score_delta: float | None = None
    activity_confidence_status: PathwayActivityConfidenceStatus | None = None
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)
    significant: bool = False
    total_member_count: int | None = Field(default=None, ge=0)
    foreground_overlap_count: int | None = Field(default=None, ge=0)
    background_member_count: int | None = Field(default=None, ge=0)
    condition_a_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    condition_b_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class CrossStudyPathwayComparisonEntry(JsonModel):
    """One cross-study pathway comparison summary."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., min_length=1)
    signal_kind: CrossStudyPathwaySignalKind
    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    member_kind: PathwayMemberKind | None = None
    study_ids: tuple[str, ...] = Field(default_factory=tuple)
    study_kinds: tuple[ProteomicsStudyKind, ...] = Field(default_factory=tuple)
    tested_study_count: int = Field(..., ge=0)
    significant_study_count: int = Field(..., ge=0)
    significant_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    non_significant_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    contrast_alignment_status: CrossStudyPathwayContrastAlignmentStatus
    anchor_condition_a: str | None = None
    anchor_condition_b: str | None = None
    comparison_status: CrossStudyPathwayComparisonStatus
    shared_signal: bool = False
    opposite_signal: bool = False
    study_specific_signal: bool = False
    normalized_significant_directions: tuple[CrossStudyPathwayDirection, ...] = Field(
        default_factory=tuple
    )
    minimum_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    maximum_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    coverage_fraction_range: float | None = Field(default=None, ge=0.0, le=1.0)
    minimum_total_member_count: int | None = Field(default=None, ge=0)
    maximum_total_member_count: int | None = Field(default=None, ge=0)
    minimum_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    maximum_enrichment_ratio: float | None = Field(default=None, ge=0.0)
    note: str = Field(..., min_length=1)


class CrossStudyPathwayComparisonSummary(JsonModel):
    """Summary over one cross-study pathway comparison pass."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    comparison_count: int = Field(..., ge=0)
    shared_signal_count: int = Field(..., ge=0)
    opposite_signal_count: int = Field(..., ge=0)
    study_specific_signal_count: int = Field(..., ge=0)
    heterogeneous_contrast_count: int = Field(..., ge=0)
    insufficient_support_count: int = Field(..., ge=0)


class CrossStudyPathwayComparisonReport(JsonModel):
    """Owned report over pathway activity and enrichment comparison across studies."""

    model_config = ConfigDict(extra="forbid")

    extracted_observations: tuple[CrossStudyPathwayObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[CrossStudyPathwayUnsupportedStudy, ...] = Field(
        default_factory=tuple
    )
    study_entries: tuple[CrossStudyPathwayStudyEntry, ...] = Field(
        default_factory=tuple
    )
    comparisons: tuple[CrossStudyPathwayComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyPathwayComparisonSummary
    note: str = Field(..., min_length=1)


def extract_cross_study_pathway_observations(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    enrichment_policy: PathwayEnrichmentCorrectionPolicy | None = None,
    minimum_absolute_activity_score_delta: float = 0.25,
) -> CrossStudyPathwayExtractionReport:
    """Extract governed pathway activity and enrichment signals from study results."""

    active_enrichment_policy = enrichment_policy or PathwayEnrichmentCorrectionPolicy()
    observations: list[CrossStudyPathwayObservation] = []
    unsupported: list[CrossStudyPathwayUnsupportedStudy] = []
    for study in studies:
        extracted = _extract_study_pathway_observations(
            study,
            enrichment_policy=active_enrichment_policy,
            minimum_absolute_activity_score_delta=minimum_absolute_activity_score_delta,
        )
        if extracted is None:
            unsupported.append(
                CrossStudyPathwayUnsupportedStudy(
                    study_id=study.study_id,
                    study_label=study.study_label,
                    study_kind=study.study_result.study_kind,
                    reason=(
                        "study result does not expose a governed biological pathway "
                        "report bundle that can be compared across studies"
                    ),
                )
            )
            continue
        observations.extend(extracted)
    return CrossStudyPathwayExtractionReport(
        observations=tuple(observations),
        unsupported_studies=tuple(unsupported),
        summary=CrossStudyPathwayExtractionSummary(
            input_study_count=len(studies),
            supported_study_count=len({entry.study_id for entry in observations}),
            unsupported_study_count=len(unsupported),
            observation_count=len(observations),
            activity_observation_count=sum(
                entry.signal_kind is CrossStudyPathwaySignalKind.ACTIVITY
                for entry in observations
            ),
            enrichment_observation_count=sum(
                entry.signal_kind is CrossStudyPathwaySignalKind.ENRICHMENT
                for entry in observations
            ),
        ),
        note=(
            "cross-study pathway extraction preserves owned pathway activity and "
            "enrichment signals with explicit member coverage instead of reducing "
            "studies to pathway-name overlap only"
        ),
    )


def build_cross_study_pathway_comparison_report(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    enrichment_policy: PathwayEnrichmentCorrectionPolicy | None = None,
    minimum_absolute_activity_score_delta: float = 0.25,
) -> CrossStudyPathwayComparisonReport:
    """Compare pathway activity and enrichment signals across studies."""

    extraction = extract_cross_study_pathway_observations(
        studies,
        enrichment_policy=enrichment_policy,
        minimum_absolute_activity_score_delta=minimum_absolute_activity_score_delta,
    )
    return build_cross_study_pathway_comparison_report_from_observations(
        extraction.observations,
        unsupported_studies=extraction.unsupported_studies,
        input_study_count=extraction.summary.input_study_count,
    )


def build_cross_study_pathway_comparison_report_from_observations(
    observations: tuple[CrossStudyPathwayObservation, ...],
    *,
    unsupported_studies: tuple[CrossStudyPathwayUnsupportedStudy, ...] = (),
    input_study_count: int | None = None,
) -> CrossStudyPathwayComparisonReport:
    """Compare extracted pathway signals across studies."""

    grouped: dict[
        tuple[str, str, str, str, str], list[CrossStudyPathwayObservation]
    ] = {}
    for observation in observations:
        grouped.setdefault(_comparison_key(observation), []).append(observation)

    study_entries: list[CrossStudyPathwayStudyEntry] = []
    comparisons: list[CrossStudyPathwayComparisonEntry] = []
    for key in sorted(grouped):
        group = tuple(
            sorted(grouped[key], key=lambda item: (item.study_id, item.observation_id))
        )
        comparison_id = _comparison_id_from_key(key)
        entries, alignment_status, anchor_condition_a, anchor_condition_b = (
            _study_entries_for_group(
                comparison_id=comparison_id,
                observations=group,
            )
        )
        study_entries.extend(entries)
        comparisons.append(
            _build_pathway_comparison_entry(
                comparison_id=comparison_id,
                entries=entries,
                alignment_status=alignment_status,
                anchor_condition_a=anchor_condition_a,
                anchor_condition_b=anchor_condition_b,
            )
        )

    return CrossStudyPathwayComparisonReport(
        extracted_observations=observations,
        unsupported_studies=unsupported_studies,
        study_entries=tuple(study_entries),
        comparisons=tuple(comparisons),
        summary=CrossStudyPathwayComparisonSummary(
            input_study_count=(
                len({entry.study_id for entry in observations})
                + len(unsupported_studies)
                if input_study_count is None
                else input_study_count
            ),
            supported_study_count=len({entry.study_id for entry in observations}),
            unsupported_study_count=len(unsupported_studies),
            observation_count=len(observations),
            comparison_count=len(comparisons),
            shared_signal_count=sum(entry.shared_signal for entry in comparisons),
            opposite_signal_count=sum(entry.opposite_signal for entry in comparisons),
            study_specific_signal_count=sum(
                entry.study_specific_signal for entry in comparisons
            ),
            heterogeneous_contrast_count=sum(
                entry.comparison_status
                is CrossStudyPathwayComparisonStatus.HETEROGENEOUS_CONTRASTS
                for entry in comparisons
            ),
            insufficient_support_count=sum(
                entry.comparison_status
                is CrossStudyPathwayComparisonStatus.INSUFFICIENT_SUPPORT
                for entry in comparisons
            ),
        ),
        note=(
            "cross-study pathway comparison preserves shared, opposite, and "
            "study-specific pathway signals while carrying member coverage differences "
            "forward into the review surface"
        ),
    )


def render_cross_study_pathway_comparison_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render cross-study pathway comparisons as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "comparison_id",
            "signal_kind",
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "study_ids",
            "study_kinds",
            "tested_study_count",
            "significant_study_count",
            "significant_study_ids",
            "non_significant_study_ids",
            "contrast_alignment_status",
            "anchor_condition_a",
            "anchor_condition_b",
            "comparison_status",
            "shared_signal",
            "opposite_signal",
            "study_specific_signal",
            "normalized_significant_directions",
            "minimum_coverage_fraction",
            "maximum_coverage_fraction",
            "coverage_fraction_range",
            "minimum_total_member_count",
            "maximum_total_member_count",
            "minimum_adjusted_p_value",
            "maximum_enrichment_ratio",
            "note",
        ]
    )
    for entry in report.comparisons:
        writer.writerow(
            [
                entry.comparison_id,
                entry.signal_kind.value,
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                "" if entry.member_kind is None else entry.member_kind.value,
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                entry.tested_study_count,
                entry.significant_study_count,
                ";".join(entry.significant_study_ids),
                ";".join(entry.non_significant_study_ids),
                entry.contrast_alignment_status.value,
                entry.anchor_condition_a or "",
                entry.anchor_condition_b or "",
                entry.comparison_status.value,
                str(entry.shared_signal).lower(),
                str(entry.opposite_signal).lower(),
                str(entry.study_specific_signal).lower(),
                ";".join(
                    direction.value
                    for direction in entry.normalized_significant_directions
                ),
                _format_float(entry.minimum_coverage_fraction),
                _format_float(entry.maximum_coverage_fraction),
                _format_float(entry.coverage_fraction_range),
                ""
                if entry.minimum_total_member_count is None
                else entry.minimum_total_member_count,
                ""
                if entry.maximum_total_member_count is None
                else entry.maximum_total_member_count,
                _format_float(entry.minimum_adjusted_p_value),
                _format_float(entry.maximum_enrichment_ratio),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_pathway_detail_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render per-study pathway comparison details as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "comparison_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "signal_kind",
            "pathway_id",
            "pathway_name",
            "source_name",
            "source_accession",
            "member_kind",
            "condition_a",
            "condition_b",
            "direction",
            "normalized_direction",
            "activity_score_delta",
            "normalized_activity_score_delta",
            "activity_confidence_status",
            "p_value",
            "adjusted_p_value",
            "enrichment_ratio",
            "significant",
            "total_member_count",
            "foreground_overlap_count",
            "background_member_count",
            "condition_a_coverage_fraction",
            "condition_b_coverage_fraction",
            "coverage_fraction",
            "note",
        ]
    )
    for entry in report.study_entries:
        writer.writerow(
            [
                entry.comparison_id,
                entry.observation_id,
                entry.study_id,
                entry.study_label or "",
                entry.study_kind.value,
                entry.signal_kind.value,
                entry.pathway_id,
                entry.pathway_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                "" if entry.member_kind is None else entry.member_kind.value,
                entry.condition_a or "",
                entry.condition_b or "",
                "" if entry.direction is None else entry.direction.value,
                ""
                if entry.normalized_direction is None
                else entry.normalized_direction.value,
                _format_float(entry.activity_score_delta),
                _format_float(entry.normalized_activity_score_delta),
                ""
                if entry.activity_confidence_status is None
                else entry.activity_confidence_status.value,
                _format_float(entry.p_value),
                _format_float(entry.adjusted_p_value),
                _format_float(entry.enrichment_ratio),
                str(entry.significant).lower(),
                "" if entry.total_member_count is None else entry.total_member_count,
                ""
                if entry.foreground_overlap_count is None
                else entry.foreground_overlap_count,
                ""
                if entry.background_member_count is None
                else entry.background_member_count,
                _format_float(entry.condition_a_coverage_fraction),
                _format_float(entry.condition_b_coverage_fraction),
                _format_float(entry.coverage_fraction),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_shared_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render shared pathway signals as TSV."""

    return _render_filtered_pathway_tsv(
        report,
        CrossStudyPathwayComparisonStatus.SHARED_SIGNAL,
    )


def render_cross_study_opposite_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render opposite pathway signals as TSV."""

    return _render_filtered_pathway_tsv(
        report,
        CrossStudyPathwayComparisonStatus.OPPOSITE_SIGNAL,
    )


def render_cross_study_study_specific_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
) -> str:
    """Render study-specific pathway signals as TSV."""

    return _render_filtered_pathway_tsv(
        report,
        CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL,
    )


def export_cross_study_pathway_comparison_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write pathway comparison summaries to TSV."""

    write_output_table_tsv(path, render_cross_study_pathway_comparison_tsv(report))


def export_cross_study_pathway_detail_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write pathway comparison details to TSV."""

    write_output_table_tsv(path, render_cross_study_pathway_detail_tsv(report))


def export_cross_study_shared_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write shared pathway signals to TSV."""

    write_output_table_tsv(path, render_cross_study_shared_pathway_signal_tsv(report))


def export_cross_study_opposite_pathway_signal_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write opposite pathway signals to TSV."""

    write_output_table_tsv(path, render_cross_study_opposite_pathway_signal_tsv(report))


def export_cross_study_study_specific_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
    path: Path,
) -> None:
    """Write study-specific pathway signals to TSV."""

    write_output_table_tsv(path, render_cross_study_study_specific_pathway_tsv(report))


def _extract_study_pathway_observations(
    study: CrossStudyProteinStudyInput,
    *,
    enrichment_policy: PathwayEnrichmentCorrectionPolicy,
    minimum_absolute_activity_score_delta: float,
) -> tuple[CrossStudyPathwayObservation, ...] | None:
    report = study.study_result.biological_report
    if report is None:
        return None
    observations: list[CrossStudyPathwayObservation] = []
    if report.pathway_activity_report is not None:
        activity_report = report.pathway_activity_report
        coverage_lookup = _activity_condition_coverage_lookup(activity_report)
        total_member_lookup = _activity_total_member_lookup(activity_report)
        for entry in activity_report.condition_comparisons:
            condition_a_coverage = coverage_lookup.get(
                (entry.pathway_id, entry.condition_a)
            )
            condition_b_coverage = coverage_lookup.get(
                (entry.pathway_id, entry.condition_b)
            )
            activity_delta = entry.activity_score_delta
            direction = (
                None
                if activity_delta is None
                else _direction_from_delta(activity_delta)
            )
            significant = (
                entry.comparison_confidence_status
                is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
                and activity_delta is not None
                and abs(activity_delta) >= minimum_absolute_activity_score_delta
            )
            observations.append(
                CrossStudyPathwayObservation(
                    observation_id=(
                        f"{study.study_id}:activity:{entry.pathway_id}:"
                        f"{entry.condition_a}_vs_{entry.condition_b}"
                    ),
                    study_id=study.study_id,
                    study_label=study.study_label,
                    study_kind=study.study_result.study_kind,
                    signal_kind=CrossStudyPathwaySignalKind.ACTIVITY,
                    pathway_id=entry.pathway_id,
                    pathway_name=entry.pathway_name,
                    source_name=entry.source_name,
                    source_accession=entry.source_accession,
                    condition_a=entry.condition_a,
                    condition_b=entry.condition_b,
                    direction=direction,
                    activity_score_delta=activity_delta,
                    activity_confidence_status=entry.comparison_confidence_status,
                    significant=significant,
                    total_member_count=total_member_lookup.get(entry.pathway_id),
                    condition_a_coverage_fraction=condition_a_coverage,
                    condition_b_coverage_fraction=condition_b_coverage,
                    coverage_fraction=_activity_coverage_fraction(
                        condition_a_coverage,
                        condition_b_coverage,
                    ),
                    note=(
                        "pathway activity comparison preserves condition-level activity "
                        "delta together with observed member coverage across the compared conditions"
                    ),
                )
            )
    if report.pathway_enrichment_report is not None:
        enrichment_report = report.pathway_enrichment_report
        for entry in enrichment_report.entries:
            adjusted_p_value = entry.adjusted_p_value
            significant = (
                adjusted_p_value is not None
                and adjusted_p_value <= enrichment_policy.max_adjusted_p_value
                and (entry.enrichment_ratio or 0.0)
                >= enrichment_policy.min_enrichment_ratio
            )
            observations.append(
                CrossStudyPathwayObservation(
                    observation_id=(
                        f"{study.study_id}:enrichment:{entry.pathway_id}:"
                        f"{entry.member_kind.value}"
                    ),
                    study_id=study.study_id,
                    study_label=study.study_label,
                    study_kind=study.study_result.study_kind,
                    signal_kind=CrossStudyPathwaySignalKind.ENRICHMENT,
                    pathway_id=entry.pathway_id,
                    pathway_name=entry.pathway_name,
                    source_name=entry.source_name,
                    source_accession=entry.source_accession,
                    member_kind=entry.member_kind,
                    p_value=entry.p_value,
                    adjusted_p_value=adjusted_p_value,
                    enrichment_ratio=entry.enrichment_ratio,
                    significant=significant,
                    foreground_overlap_count=entry.foreground_overlap_count,
                    background_member_count=entry.background_member_count,
                    total_member_count=entry.background_member_count,
                    coverage_fraction=_safe_fraction(
                        entry.foreground_overlap_count,
                        entry.background_member_count,
                    ),
                    note=(
                        "pathway enrichment comparison preserves overlap and background "
                        "member counts so cross-study pathway calls report coverage differences explicitly"
                    ),
                )
            )
    if not observations:
        return None
    return tuple(observations)


def _activity_condition_coverage_lookup(
    report: PathwayActivityReport,
) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for entry in report.sample_scores:
        if entry.condition is None:
            continue
        grouped.setdefault((entry.pathway_id, entry.condition), []).append(
            entry.observed_fraction
        )
    return {
        key: round(float(mean(values)), 6) for key, values in grouped.items() if values
    }


def _activity_total_member_lookup(report: PathwayActivityReport) -> dict[str, int]:
    totals: dict[str, int] = {}
    for entry in report.sample_scores:
        totals.setdefault(entry.pathway_id, entry.total_member_count)
    return totals


def _comparison_key(
    observation: CrossStudyPathwayObservation,
) -> tuple[str, str, str, str, str]:
    return (
        observation.signal_kind.value,
        observation.pathway_id,
        observation.source_accession or "",
        observation.source_name or "",
        "" if observation.member_kind is None else observation.member_kind.value,
    )


def _comparison_id_from_key(key: tuple[str, str, str, str, str]) -> str:
    signal_kind, pathway_id, source_accession, source_name, member_kind = key
    source_token = source_accession or source_name or "unsourced"
    member_token = member_kind or "all_members"
    return (
        f"{_stable_token(signal_kind)}_pathway_"
        f"{_stable_token(source_token)}_"
        f"{_stable_token(pathway_id)}_"
        f"{_stable_token(member_token)}"
    )


def _stable_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token or "unspecified"


def _study_entries_for_group(
    *,
    comparison_id: str,
    observations: tuple[CrossStudyPathwayObservation, ...],
) -> tuple[
    tuple[CrossStudyPathwayStudyEntry, ...],
    CrossStudyPathwayContrastAlignmentStatus,
    str | None,
    str | None,
]:
    if not observations:
        return (), CrossStudyPathwayContrastAlignmentStatus.NOT_APPLICABLE, None, None
    first = observations[0]
    if first.signal_kind is CrossStudyPathwaySignalKind.ENRICHMENT:
        return (
            tuple(
                _study_entry_from_observation(
                    comparison_id=comparison_id,
                    observation=entry,
                    normalized_direction=None,
                    normalized_delta=None,
                )
                for entry in observations
            ),
            CrossStudyPathwayContrastAlignmentStatus.NOT_APPLICABLE,
            None,
            None,
        )
    anchor_condition_a = first.condition_a
    anchor_condition_b = first.condition_b
    if anchor_condition_a is None or anchor_condition_b is None:
        return (
            tuple(
                _study_entry_from_observation(
                    comparison_id=comparison_id,
                    observation=entry,
                    normalized_direction=None,
                    normalized_delta=None,
                )
                for entry in observations
            ),
            CrossStudyPathwayContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS,
            anchor_condition_a,
            anchor_condition_b,
        )
    entries: list[CrossStudyPathwayStudyEntry] = []
    reversed_seen = False
    for observation in observations:
        if (
            observation.condition_a == anchor_condition_a
            and observation.condition_b == anchor_condition_b
        ):
            entries.append(
                _study_entry_from_observation(
                    comparison_id=comparison_id,
                    observation=observation,
                    normalized_direction=observation.direction,
                    normalized_delta=observation.activity_score_delta,
                )
            )
            continue
        if (
            observation.condition_a == anchor_condition_b
            and observation.condition_b == anchor_condition_a
        ):
            reversed_seen = True
            normalized_delta = (
                None
                if observation.activity_score_delta is None
                else -observation.activity_score_delta
            )
            entries.append(
                _study_entry_from_observation(
                    comparison_id=comparison_id,
                    observation=observation,
                    normalized_direction=(
                        None
                        if normalized_delta is None
                        else _direction_from_delta(normalized_delta)
                    ),
                    normalized_delta=normalized_delta,
                )
            )
            continue
        return (
            tuple(
                _study_entry_from_observation(
                    comparison_id=comparison_id,
                    observation=entry,
                    normalized_direction=None,
                    normalized_delta=None,
                )
                for entry in observations
            ),
            CrossStudyPathwayContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS,
            anchor_condition_a,
            anchor_condition_b,
        )
    return (
        tuple(entries),
        (
            CrossStudyPathwayContrastAlignmentStatus.REVERSED_ORDER_NORMALIZED
            if reversed_seen
            else CrossStudyPathwayContrastAlignmentStatus.SAME_ORDERED_CONTRAST
        ),
        anchor_condition_a,
        anchor_condition_b,
    )


def _study_entry_from_observation(
    *,
    comparison_id: str,
    observation: CrossStudyPathwayObservation,
    normalized_direction: CrossStudyPathwayDirection | None,
    normalized_delta: float | None,
) -> CrossStudyPathwayStudyEntry:
    return CrossStudyPathwayStudyEntry(
        comparison_id=comparison_id,
        observation_id=observation.observation_id,
        study_id=observation.study_id,
        study_label=observation.study_label,
        study_kind=observation.study_kind,
        signal_kind=observation.signal_kind,
        pathway_id=observation.pathway_id,
        pathway_name=observation.pathway_name,
        source_name=observation.source_name,
        source_accession=observation.source_accession,
        member_kind=observation.member_kind,
        condition_a=observation.condition_a,
        condition_b=observation.condition_b,
        direction=observation.direction,
        normalized_direction=normalized_direction,
        activity_score_delta=observation.activity_score_delta,
        normalized_activity_score_delta=normalized_delta,
        activity_confidence_status=observation.activity_confidence_status,
        p_value=observation.p_value,
        adjusted_p_value=observation.adjusted_p_value,
        enrichment_ratio=observation.enrichment_ratio,
        significant=observation.significant,
        total_member_count=observation.total_member_count,
        foreground_overlap_count=observation.foreground_overlap_count,
        background_member_count=observation.background_member_count,
        condition_a_coverage_fraction=observation.condition_a_coverage_fraction,
        condition_b_coverage_fraction=observation.condition_b_coverage_fraction,
        coverage_fraction=observation.coverage_fraction,
        note=observation.note,
    )


def _build_pathway_comparison_entry(
    *,
    comparison_id: str,
    entries: tuple[CrossStudyPathwayStudyEntry, ...],
    alignment_status: CrossStudyPathwayContrastAlignmentStatus,
    anchor_condition_a: str | None,
    anchor_condition_b: str | None,
) -> CrossStudyPathwayComparisonEntry:
    first = entries[0]
    significant_entries = tuple(entry for entry in entries if entry.significant)
    directions = tuple(
        entry.normalized_direction
        for entry in significant_entries
        if entry.normalized_direction is not None
    )
    direction_set = {
        direction
        for direction in directions
        if direction in {CrossStudyPathwayDirection.UP, CrossStudyPathwayDirection.DOWN}
    }
    if first.signal_kind is CrossStudyPathwaySignalKind.ACTIVITY:
        if (
            alignment_status
            is CrossStudyPathwayContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
        ):
            status = CrossStudyPathwayComparisonStatus.HETEROGENEOUS_CONTRASTS
            note = (
                "studies compared different condition pairs, so pathway activity deltas "
                "were not merged into shared or opposite signals"
            )
        elif len(significant_entries) >= 2 and len(direction_set) > 1:
            status = CrossStudyPathwayComparisonStatus.OPPOSITE_SIGNAL
            note = (
                "high-confidence pathway activity deltas pointed in opposite "
                "directions across studies after contrast normalization"
            )
        elif len(significant_entries) >= 2 and len(direction_set) == 1:
            status = CrossStudyPathwayComparisonStatus.SHARED_SIGNAL
            note = (
                "at least two studies supported the same high-confidence pathway "
                "activity direction after contrast normalization"
            )
        elif len(significant_entries) == 1 and len(entries) >= 2:
            status = CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL
            note = (
                "only one study supported a high-confidence pathway activity signal "
                "while the other studies did not"
            )
        else:
            status = CrossStudyPathwayComparisonStatus.INSUFFICIENT_SUPPORT
            note = (
                "cross-study pathway activity support was not strong enough to call a "
                "shared, opposite, or study-specific signal"
            )
    else:
        if len(significant_entries) >= 2:
            status = CrossStudyPathwayComparisonStatus.SHARED_SIGNAL
            note = (
                "at least two studies supported pathway enrichment for the same "
                "pathway and member-kind surface"
            )
        elif len(significant_entries) == 1 and len(entries) >= 2:
            status = CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL
            note = (
                "only one study supported pathway enrichment while the others did not"
            )
        else:
            status = CrossStudyPathwayComparisonStatus.INSUFFICIENT_SUPPORT
            note = (
                "cross-study pathway enrichment support was not strong enough to call "
                "a shared or study-specific signal"
            )
    coverage_values = [
        entry.coverage_fraction
        for entry in entries
        if entry.coverage_fraction is not None
    ]
    total_member_counts = [
        entry.total_member_count
        for entry in entries
        if entry.total_member_count is not None
    ]
    adjusted_values = [
        value
        for entry in entries
        for value in (
            (
                entry.adjusted_p_value
                if entry.adjusted_p_value is not None
                else entry.p_value
            ),
        )
        if value is not None
    ]
    enrichment_ratios = [
        entry.enrichment_ratio
        for entry in entries
        if entry.enrichment_ratio is not None
    ]
    return CrossStudyPathwayComparisonEntry(
        comparison_id=comparison_id,
        signal_kind=first.signal_kind,
        pathway_id=first.pathway_id,
        pathway_name=first.pathway_name,
        source_name=first.source_name,
        source_accession=first.source_accession,
        member_kind=first.member_kind,
        study_ids=tuple(entry.study_id for entry in entries),
        study_kinds=tuple(entry.study_kind for entry in entries),
        tested_study_count=len(entries),
        significant_study_count=len(significant_entries),
        significant_study_ids=tuple(entry.study_id for entry in significant_entries),
        non_significant_study_ids=tuple(
            entry.study_id for entry in entries if not entry.significant
        ),
        contrast_alignment_status=alignment_status,
        anchor_condition_a=anchor_condition_a,
        anchor_condition_b=anchor_condition_b,
        comparison_status=status,
        shared_signal=status is CrossStudyPathwayComparisonStatus.SHARED_SIGNAL,
        opposite_signal=status is CrossStudyPathwayComparisonStatus.OPPOSITE_SIGNAL,
        study_specific_signal=status
        is CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL,
        normalized_significant_directions=directions,
        minimum_coverage_fraction=min(coverage_values, default=None),
        maximum_coverage_fraction=max(coverage_values, default=None),
        coverage_fraction_range=(
            None if not coverage_values else max(coverage_values) - min(coverage_values)
        ),
        minimum_total_member_count=min(total_member_counts, default=None),
        maximum_total_member_count=max(total_member_counts, default=None),
        minimum_adjusted_p_value=min(adjusted_values, default=None),
        maximum_enrichment_ratio=max(enrichment_ratios, default=None),
        note=note,
    )


def _direction_from_delta(delta: float) -> CrossStudyPathwayDirection:
    if delta > 0:
        return CrossStudyPathwayDirection.UP
    if delta < 0:
        return CrossStudyPathwayDirection.DOWN
    return CrossStudyPathwayDirection.FLAT


def _activity_coverage_fraction(
    condition_a_coverage: float | None,
    condition_b_coverage: float | None,
) -> float | None:
    values = [
        value
        for value in (condition_a_coverage, condition_b_coverage)
        if value is not None
    ]
    return None if not values else round(float(mean(values)), 6)


def _safe_fraction(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _render_filtered_pathway_tsv(
    report: CrossStudyPathwayComparisonReport,
    status: CrossStudyPathwayComparisonStatus,
) -> str:
    filtered = report.model_copy(
        update={
            "comparisons": tuple(
                entry
                for entry in report.comparisons
                if entry.comparison_status is status
            )
        }
    )
    return render_cross_study_pathway_comparison_tsv(filtered)


def _format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


__all__ = [
    "CrossStudyPathwayComparisonEntry",
    "CrossStudyPathwayComparisonReport",
    "CrossStudyPathwayComparisonStatus",
    "CrossStudyPathwayComparisonSummary",
    "CrossStudyPathwayContrastAlignmentStatus",
    "CrossStudyPathwayDirection",
    "CrossStudyPathwayExtractionReport",
    "CrossStudyPathwayExtractionSummary",
    "CrossStudyPathwayObservation",
    "CrossStudyPathwaySignalKind",
    "CrossStudyPathwayStudyEntry",
    "CrossStudyPathwayUnsupportedStudy",
    "build_cross_study_pathway_comparison_report",
    "build_cross_study_pathway_comparison_report_from_observations",
    "export_cross_study_opposite_pathway_signal_tsv",
    "export_cross_study_pathway_comparison_tsv",
    "export_cross_study_pathway_detail_tsv",
    "export_cross_study_shared_pathway_signal_tsv",
    "export_cross_study_study_specific_pathway_tsv",
    "extract_cross_study_pathway_observations",
    "render_cross_study_opposite_pathway_signal_tsv",
    "render_cross_study_pathway_comparison_tsv",
    "render_cross_study_pathway_detail_tsv",
    "render_cross_study_shared_pathway_signal_tsv",
    "render_cross_study_study_specific_pathway_tsv",
]
