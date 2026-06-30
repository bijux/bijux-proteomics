# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study protein effect comparison over owned study-result surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import OrthologRecord
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialResultRobustnessQcStatus,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinHarmonizationReport,
    CrossStudyProteinHarmonizedEntry,
    CrossStudyProteinObservation,
    CrossStudyProteinObservationSourceKind,
    CrossStudyProteinStudyInput,
    UnsupportedCrossStudyProteinStudy,
    build_cross_study_protein_harmonization_report_from_observations,
)
from bijux_proteomics.workflow.studies.study_result import ProteomicsStudyKind
from bijux_proteomics_foundation import JsonModel


class CrossStudyEffectDirection(StrEnum):
    """Stable effect directions over one study-specific protein result."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class CrossStudyEffectContrastAlignmentStatus(StrEnum):
    """Whether study contrasts can be normalized onto one shared direction surface."""

    SAME_ORDERED_CONTRAST = "same_ordered_contrast"
    REVERSED_ORDER_NORMALIZED = "reversed_order_normalized"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"


class CrossStudyEffectComparisonStatus(StrEnum):
    """Stable cross-study effect classes over one harmonized protein group."""

    REPLICATED_HIT = "replicated_hit"
    STUDY_SPECIFIC_HIT = "study_specific_hit"
    CONFLICTING_HIT = "conflicting_hit"
    HETEROGENEOUS_CONTRASTS = "heterogeneous_contrasts"
    INSUFFICIENT_SUPPORT = "insufficient_support"


class CrossStudyProteinEffectObservation(JsonModel):
    """One protein-level study effect that can participate in cross-study comparison."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    source_kind: CrossStudyProteinObservationSourceKind
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    contrast_label: str | None = None
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    log2_fold_change: float
    direction: CrossStudyEffectDirection
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    significant: bool = False
    note: str = Field(..., min_length=1)


class CrossStudyEffectUnsupportedStudy(JsonModel):
    """One study result that could not contribute protein effect comparisons."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    reason: str = Field(..., min_length=1)


class CrossStudyProteinEffectExtractionSummary(JsonModel):
    """Summary over extracted cross-study protein effects."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    observation_count: int = Field(..., ge=0)
    biological_report_observation_count: int = Field(..., ge=0)
    label_based_observation_count: int = Field(..., ge=0)


class CrossStudyProteinEffectExtractionReport(JsonModel):
    """Owned extraction report over cross-study protein effects."""

    model_config = ConfigDict(extra="forbid")

    observations: tuple[CrossStudyProteinEffectObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[CrossStudyEffectUnsupportedStudy, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyProteinEffectExtractionSummary
    note: str = Field(..., min_length=1)


class CrossStudyProteinEffectStudyEntry(JsonModel):
    """One study-specific effect aligned under one harmonized protein group."""

    model_config = ConfigDict(extra="forbid")

    harmonized_id: str = Field(..., min_length=1)
    observation_id: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    study_label: str | None = None
    study_kind: ProteomicsStudyKind
    species: str | None = None
    source_kind: CrossStudyProteinObservationSourceKind
    source_surface: str = Field(..., min_length=1)
    source_entity_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    contrast_label: str | None = None
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    log2_fold_change: float
    direction: CrossStudyEffectDirection
    normalized_log2_fold_change: float | None = None
    normalized_direction: CrossStudyEffectDirection | None = None
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None = None
    significant: bool = False
    note: str = Field(..., min_length=1)


class CrossStudyProteinEffectComparisonEntry(JsonModel):
    """One harmonized protein summary across comparable study effects."""

    model_config = ConfigDict(extra="forbid")

    harmonized_id: str = Field(..., min_length=1)
    representative_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    study_ids: tuple[str, ...] = Field(default_factory=tuple)
    study_kinds: tuple[ProteomicsStudyKind, ...] = Field(default_factory=tuple)
    tested_study_count: int = Field(..., ge=0)
    significant_study_count: int = Field(..., ge=0)
    significant_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    non_significant_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    contrast_alignment_status: CrossStudyEffectContrastAlignmentStatus
    anchor_condition_a: str | None = None
    anchor_condition_b: str | None = None
    comparison_status: CrossStudyEffectComparisonStatus
    replicated_hit: bool = False
    study_specific_hit: bool = False
    conflicting_hit: bool = False
    conflicting_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    normalized_significant_directions: tuple[CrossStudyEffectDirection, ...] = Field(
        default_factory=tuple
    )
    min_log2_fold_change: float | None = None
    max_log2_fold_change: float | None = None
    median_absolute_log2_fold_change: float | None = Field(default=None, ge=0.0)
    min_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    median_robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    low_robustness_study_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CrossStudyProteinEffectComparisonSummary(JsonModel):
    """Summary over one cross-study effect comparison pass."""

    model_config = ConfigDict(extra="forbid")

    input_study_count: int = Field(..., ge=0)
    supported_study_count: int = Field(..., ge=0)
    unsupported_study_count: int = Field(..., ge=0)
    effect_observation_count: int = Field(..., ge=0)
    harmonized_group_count: int = Field(..., ge=0)
    replicated_hit_count: int = Field(..., ge=0)
    study_specific_hit_count: int = Field(..., ge=0)
    conflicting_hit_count: int = Field(..., ge=0)
    heterogeneous_contrast_count: int = Field(..., ge=0)
    insufficient_support_count: int = Field(..., ge=0)
    low_robustness_comparison_count: int = Field(..., ge=0)


class CrossStudyProteinEffectComparisonReport(JsonModel):
    """Owned report over cross-study protein effect comparison."""

    model_config = ConfigDict(extra="forbid")

    extracted_effects: tuple[CrossStudyProteinEffectObservation, ...] = Field(
        default_factory=tuple
    )
    unsupported_studies: tuple[CrossStudyEffectUnsupportedStudy, ...] = Field(
        default_factory=tuple
    )
    harmonization_report: CrossStudyProteinHarmonizationReport
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...] = Field(
        default_factory=tuple
    )
    comparisons: tuple[CrossStudyProteinEffectComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CrossStudyProteinEffectComparisonSummary
    note: str = Field(..., min_length=1)


def extract_cross_study_protein_effect_observations(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    significance_threshold: float = 0.05,
) -> CrossStudyProteinEffectExtractionReport:
    """Extract protein-level study effects from owned study-result surfaces."""

    observations: list[CrossStudyProteinEffectObservation] = []
    unsupported: list[CrossStudyEffectUnsupportedStudy] = []
    for study in studies:
        extracted = _extract_study_effect_observations(
            study,
            significance_threshold=significance_threshold,
        )
        if extracted is not None:
            observations.extend(extracted)
            continue
        unsupported.append(
            CrossStudyEffectUnsupportedStudy(
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                reason=(
                    "study result does not expose one governed two-condition protein "
                    "effect surface that can be compared across studies"
                ),
            )
        )
    summary = CrossStudyProteinEffectExtractionSummary(
        input_study_count=len(studies),
        supported_study_count=len({entry.study_id for entry in observations}),
        unsupported_study_count=len(unsupported),
        observation_count=len(observations),
        biological_report_observation_count=sum(
            entry.source_kind
            is CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD
            for entry in observations
        ),
        label_based_observation_count=sum(
            entry.source_kind
            is CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
            for entry in observations
        ),
    )
    return CrossStudyProteinEffectExtractionReport(
        observations=tuple(observations),
        unsupported_studies=tuple(unsupported),
        summary=summary,
        note=(
            "cross-study protein effect extraction preserves one comparable protein "
            "effect surface per supported study and leaves unsupported study classes explicit"
        ),
    )


def build_cross_study_effect_comparison_report(
    studies: tuple[CrossStudyProteinStudyInput, ...],
    *,
    ortholog_records: tuple[OrthologRecord, ...] = (),
    significance_threshold: float = 0.05,
    low_robustness_threshold: float = 0.5,
) -> CrossStudyProteinEffectComparisonReport:
    """Compare protein effects across harmonized study-result surfaces."""

    extraction = extract_cross_study_protein_effect_observations(
        studies,
        significance_threshold=significance_threshold,
    )
    return build_cross_study_effect_comparison_report_from_observations(
        extraction.observations,
        unsupported_studies=extraction.unsupported_studies,
        ortholog_records=ortholog_records,
        input_study_count=extraction.summary.input_study_count,
        significance_threshold=significance_threshold,
        low_robustness_threshold=low_robustness_threshold,
    )


def build_cross_study_effect_comparison_report_from_observations(
    observations: tuple[CrossStudyProteinEffectObservation, ...],
    *,
    unsupported_studies: tuple[CrossStudyEffectUnsupportedStudy, ...] = (),
    ortholog_records: tuple[OrthologRecord, ...] = (),
    input_study_count: int | None = None,
    significance_threshold: float = 0.05,
    low_robustness_threshold: float = 0.5,
) -> CrossStudyProteinEffectComparisonReport:
    """Compare effect directions, FDR, and robustness across harmonized proteins."""

    identity_observations = tuple(
        _identity_observation_from_effect(entry) for entry in observations
    )
    harmonization_report = (
        build_cross_study_protein_harmonization_report_from_observations(
            identity_observations,
            ortholog_records=ortholog_records,
            unsupported_studies=tuple(
                UnsupportedCrossStudyProteinStudy(
                    study_id=entry.study_id,
                    study_label=entry.study_label,
                    study_kind=entry.study_kind,
                    reason=entry.reason,
                )
                for entry in unsupported_studies
            ),
            input_study_count=input_study_count,
        )
    )
    observation_lookup = {entry.observation_id: entry for entry in observations}
    grouped_harmonized_entries: dict[str, list[CrossStudyProteinHarmonizedEntry]] = {}
    for entry in harmonization_report.harmonized_entries:
        grouped_harmonized_entries.setdefault(entry.harmonized_id, []).append(entry)

    study_entries: list[CrossStudyProteinEffectStudyEntry] = []
    comparison_entries: list[CrossStudyProteinEffectComparisonEntry] = []
    for harmonized_id in sorted(grouped_harmonized_entries):
        members = sorted(
            grouped_harmonized_entries[harmonized_id],
            key=lambda item: (item.study_id, item.observation_id),
        )
        entries = tuple(
            _study_entry_from_effect_member(
                harmonized_id=harmonized_id,
                member=member,
                observation=observation_lookup[member.observation_id],
            )
            for member in members
        )
        study_entries.extend(entries)
        comparison_entries.append(
            _build_effect_comparison_entry(
                harmonized_id=harmonized_id,
                entries=entries,
                significance_threshold=significance_threshold,
                low_robustness_threshold=low_robustness_threshold,
            )
        )

    summary = CrossStudyProteinEffectComparisonSummary(
        input_study_count=(
            len({entry.study_id for entry in observations}) + len(unsupported_studies)
            if input_study_count is None
            else input_study_count
        ),
        supported_study_count=len({entry.study_id for entry in observations}),
        unsupported_study_count=len(unsupported_studies),
        effect_observation_count=len(observations),
        harmonized_group_count=len(comparison_entries),
        replicated_hit_count=sum(
            entry.comparison_status is CrossStudyEffectComparisonStatus.REPLICATED_HIT
            for entry in comparison_entries
        ),
        study_specific_hit_count=sum(
            entry.comparison_status
            is CrossStudyEffectComparisonStatus.STUDY_SPECIFIC_HIT
            for entry in comparison_entries
        ),
        conflicting_hit_count=sum(
            entry.comparison_status is CrossStudyEffectComparisonStatus.CONFLICTING_HIT
            for entry in comparison_entries
        ),
        heterogeneous_contrast_count=sum(
            entry.comparison_status
            is CrossStudyEffectComparisonStatus.HETEROGENEOUS_CONTRASTS
            for entry in comparison_entries
        ),
        insufficient_support_count=sum(
            entry.comparison_status
            is CrossStudyEffectComparisonStatus.INSUFFICIENT_SUPPORT
            for entry in comparison_entries
        ),
        low_robustness_comparison_count=sum(
            bool(entry.low_robustness_study_ids) for entry in comparison_entries
        ),
    )
    return CrossStudyProteinEffectComparisonReport(
        extracted_effects=observations,
        unsupported_studies=unsupported_studies,
        harmonization_report=harmonization_report,
        study_entries=tuple(study_entries),
        comparisons=tuple(comparison_entries),
        summary=summary,
        note=(
            "cross-study protein effect comparison harmonizes protein identities first, "
            "then compares log2 fold change, direction, FDR, and robustness while "
            "preserving conflicting and study-specific outcomes explicitly"
        ),
    )


def render_cross_study_effect_comparison_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render one cross-study protein effect comparison report as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "representative_protein_refs",
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
            "replicated_hit",
            "study_specific_hit",
            "conflicting_hit",
            "conflicting_study_ids",
            "normalized_significant_directions",
            "min_log2_fold_change",
            "max_log2_fold_change",
            "median_absolute_log2_fold_change",
            "min_adjusted_p_value",
            "median_robustness_score",
            "low_robustness_study_ids",
            "note",
        ]
    )
    for entry in report.comparisons:
        writer.writerow(
            [
                entry.harmonized_id,
                ";".join(entry.representative_protein_refs),
                ";".join(entry.study_ids),
                ";".join(kind.value for kind in entry.study_kinds),
                entry.tested_study_count,
                entry.significant_study_count,
                ";".join(entry.significant_study_ids),
                ";".join(entry.non_significant_study_ids),
                entry.contrast_alignment_status.value,
                "" if entry.anchor_condition_a is None else entry.anchor_condition_a,
                "" if entry.anchor_condition_b is None else entry.anchor_condition_b,
                entry.comparison_status.value,
                str(entry.replicated_hit).lower(),
                str(entry.study_specific_hit).lower(),
                str(entry.conflicting_hit).lower(),
                ";".join(entry.conflicting_study_ids),
                ";".join(
                    direction.value
                    for direction in entry.normalized_significant_directions
                ),
                _format_float(entry.min_log2_fold_change),
                _format_float(entry.max_log2_fold_change),
                _format_float(entry.median_absolute_log2_fold_change),
                _format_float(entry.min_adjusted_p_value),
                _format_float(entry.median_robustness_score),
                ";".join(entry.low_robustness_study_ids),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_effect_detail_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render one per-study detail table for cross-study effect comparison."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "harmonized_id",
            "observation_id",
            "study_id",
            "study_label",
            "study_kind",
            "species",
            "source_kind",
            "source_surface",
            "source_entity_id",
            "representative_protein_ref",
            "protein_refs",
            "accession_aliases",
            "gene_symbol",
            "contrast_label",
            "condition_a",
            "condition_b",
            "log2_fold_change",
            "direction",
            "normalized_log2_fold_change",
            "normalized_direction",
            "p_value",
            "adjusted_p_value",
            "standard_error",
            "confidence_interval_low",
            "confidence_interval_high",
            "robustness_score",
            "robustness_qc_status",
            "significant",
            "note",
        ]
    )
    for entry in report.study_entries:
        writer.writerow(
            [
                entry.harmonized_id,
                entry.observation_id,
                entry.study_id,
                "" if entry.study_label is None else entry.study_label,
                entry.study_kind.value,
                "" if entry.species is None else entry.species,
                entry.source_kind.value,
                entry.source_surface,
                entry.source_entity_id,
                entry.representative_protein_ref,
                ";".join(entry.protein_refs),
                ";".join(entry.accession_aliases),
                "" if entry.gene_symbol is None else entry.gene_symbol,
                "" if entry.contrast_label is None else entry.contrast_label,
                entry.condition_a,
                entry.condition_b,
                _format_float(entry.log2_fold_change),
                entry.direction.value,
                _format_float(entry.normalized_log2_fold_change),
                ""
                if entry.normalized_direction is None
                else entry.normalized_direction.value,
                _format_float(entry.p_value),
                _format_float(entry.adjusted_p_value),
                _format_float(entry.standard_error),
                _format_float(entry.confidence_interval_low),
                _format_float(entry.confidence_interval_high),
                _format_float(entry.robustness_score),
                (
                    ""
                    if entry.robustness_qc_status is None
                    else entry.robustness_qc_status.value
                ),
                str(entry.significant).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_replicated_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only replicated cross-study protein hits as TSV."""

    return _render_filtered_effect_tsv(
        report,
        CrossStudyEffectComparisonStatus.REPLICATED_HIT,
    )


def render_cross_study_study_specific_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only study-specific cross-study protein hits as TSV."""

    return _render_filtered_effect_tsv(
        report,
        CrossStudyEffectComparisonStatus.STUDY_SPECIFIC_HIT,
    )


def render_cross_study_conflicting_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
) -> str:
    """Render only conflicting cross-study protein hits as TSV."""

    return _render_filtered_effect_tsv(
        report,
        CrossStudyEffectComparisonStatus.CONFLICTING_HIT,
    )


def export_cross_study_effect_comparison_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write cross-study effect comparison summaries to TSV."""

    write_output_table_tsv(path, render_cross_study_effect_comparison_tsv(report))


def export_cross_study_effect_detail_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write per-study cross-study effect details to TSV."""

    write_output_table_tsv(path, render_cross_study_effect_detail_tsv(report))


def export_cross_study_replicated_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write replicated cross-study hits to TSV."""

    write_output_table_tsv(path, render_cross_study_replicated_hit_tsv(report))


def export_cross_study_study_specific_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write study-specific cross-study hits to TSV."""

    write_output_table_tsv(path, render_cross_study_study_specific_hit_tsv(report))


def export_cross_study_conflicting_hit_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    path: Path,
) -> None:
    """Write conflicting cross-study hits to TSV."""

    write_output_table_tsv(path, render_cross_study_conflicting_hit_tsv(report))


def _extract_study_effect_observations(
    study: CrossStudyProteinStudyInput,
    *,
    significance_threshold: float,
) -> tuple[CrossStudyProteinEffectObservation, ...] | None:
    if study.study_result.biological_report is not None:
        return _extract_biological_report_effects(
            study,
            significance_threshold=significance_threshold,
        )
    if (
        study.study_result.label_based_report is not None
        and study.study_result.label_based_report.differential_analysis_report.differential_abundance_report
        is not None
    ):
        return _extract_label_based_effects(
            study,
            significance_threshold=significance_threshold,
        )
    return None


def _extract_biological_report_effects(
    study: CrossStudyProteinStudyInput,
    *,
    significance_threshold: float,
) -> tuple[CrossStudyProteinEffectObservation, ...]:
    report = study.study_result.biological_report
    if report is None:
        raise RuntimeError(
            "cross-study biological effect extraction requires a biological report"
        )
    differential_by_entity = {
        entry.entity_id: entry for entry in report.differential_report.entries
    }
    observations: list[CrossStudyProteinEffectObservation] = []
    for card in report.protein_cards.cards:
        differential_entry = differential_by_entity.get(card.protein_group_id)
        adjusted_p_value = (
            card.differential_result.adjusted_p_value
            if differential_entry is None or differential_entry.adjusted_p_value is None
            else differential_entry.adjusted_p_value
        )
        p_value = (
            card.differential_result.p_value
            if differential_entry is None
            else differential_entry.p_value
        )
        observations.append(
            CrossStudyProteinEffectObservation(
                observation_id=f"{study.study_id}:{card.card_id}",
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                species=study.species or card.annotation.organism,
                source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id=card.card_id,
                representative_protein_ref=card.representative_protein_ref,
                protein_refs=card.protein_refs,
                accession_aliases=card.annotation.accession_aliases,
                gene_symbol=card.annotation.gene_symbol,
                contrast_label=None,
                condition_a=card.differential_result.condition_a,
                condition_b=card.differential_result.condition_b,
                log2_fold_change=card.differential_result.log2_fold_change,
                direction=_direction_from_log2_fold_change(
                    card.differential_result.log2_fold_change
                ),
                p_value=p_value,
                adjusted_p_value=adjusted_p_value,
                standard_error=card.differential_result.standard_error,
                confidence_interval_low=card.differential_result.confidence_interval_low,
                confidence_interval_high=card.differential_result.confidence_interval_high,
                robustness_score=(
                    None
                    if differential_entry is None
                    else differential_entry.robustness_score
                ),
                robustness_qc_status=(
                    None
                    if differential_entry is None
                    else differential_entry.robustness_qc_status
                ),
                significant=_is_significant(
                    adjusted_p_value=adjusted_p_value,
                    p_value=p_value,
                    threshold=significance_threshold,
                ),
                note=(
                    "biological protein cards preserve the protein-level differential "
                    "surface and inherit robustness from the owned differential report"
                ),
            )
        )
    return tuple(observations)


def _extract_label_based_effects(
    study: CrossStudyProteinStudyInput,
    *,
    significance_threshold: float,
) -> tuple[CrossStudyProteinEffectObservation, ...]:
    report = study.study_result.label_based_report
    if report is None:
        raise RuntimeError(
            "cross-study label-based effect extraction requires a label-based report"
        )
    differential_report = (
        report.differential_analysis_report.differential_abundance_report
    )
    if differential_report is None:
        raise RuntimeError(
            "cross-study label-based effect extraction requires a differential abundance report"
        )
    matrix_rows = {
        row.entity_id: row
        for row in report.differential_analysis_report.normalized_matrix.rows
    }
    observations: list[CrossStudyProteinEffectObservation] = []
    for entry in differential_report.entries:
        row = matrix_rows.get(entry.entity_id)
        protein_refs = () if row is None else row.protein_refs
        representative_protein_ref = (
            protein_refs[0] if protein_refs else entry.entity_id
        )
        observations.append(
            CrossStudyProteinEffectObservation(
                observation_id=f"{study.study_id}:{entry.entity_id}",
                study_id=study.study_id,
                study_label=study.study_label,
                study_kind=study.study_result.study_kind,
                species=study.species,
                source_kind=(
                    CrossStudyProteinObservationSourceKind.LABEL_BASED_DIFFERENTIAL_ROW
                ),
                source_surface="label_based_differential_report",
                source_entity_id=entry.entity_id,
                representative_protein_ref=representative_protein_ref,
                protein_refs=protein_refs,
                accession_aliases=(),
                gene_symbol=None,
                contrast_label=differential_report.contrast_name,
                condition_a=entry.condition_a,
                condition_b=entry.condition_b,
                log2_fold_change=entry.log2_fold_change,
                direction=_direction_from_log2_fold_change(entry.log2_fold_change),
                p_value=entry.p_value,
                adjusted_p_value=entry.adjusted_p_value,
                standard_error=entry.standard_error,
                confidence_interval_low=entry.confidence_interval_low,
                confidence_interval_high=entry.confidence_interval_high,
                robustness_score=entry.robustness_score,
                robustness_qc_status=entry.robustness_qc_status,
                significant=_is_significant(
                    adjusted_p_value=entry.adjusted_p_value,
                    p_value=entry.p_value,
                    threshold=significance_threshold,
                ),
                note=(
                    "label-based differential analysis preserves protein-level "
                    "fold change, FDR, and robustness directly on the owned result row"
                ),
            )
        )
    return tuple(observations)


def _identity_observation_from_effect(
    observation: CrossStudyProteinEffectObservation,
) -> CrossStudyProteinObservation:
    return CrossStudyProteinObservation(
        observation_id=observation.observation_id,
        study_id=observation.study_id,
        study_label=observation.study_label,
        study_kind=observation.study_kind,
        species=observation.species,
        source_kind=observation.source_kind,
        source_surface=observation.source_surface,
        source_entity_id=observation.source_entity_id,
        representative_protein_ref=observation.representative_protein_ref,
        protein_refs=observation.protein_refs,
        accession_aliases=observation.accession_aliases,
        gene_symbol=observation.gene_symbol,
        note=observation.note,
    )


def _study_entry_from_effect_member(
    *,
    harmonized_id: str,
    member: CrossStudyProteinHarmonizedEntry,
    observation: CrossStudyProteinEffectObservation,
) -> CrossStudyProteinEffectStudyEntry:
    return CrossStudyProteinEffectStudyEntry(
        harmonized_id=harmonized_id,
        observation_id=observation.observation_id,
        study_id=observation.study_id,
        study_label=observation.study_label,
        study_kind=observation.study_kind,
        species=observation.species,
        source_kind=observation.source_kind,
        source_surface=observation.source_surface,
        source_entity_id=observation.source_entity_id,
        representative_protein_ref=observation.representative_protein_ref,
        protein_refs=observation.protein_refs,
        accession_aliases=observation.accession_aliases,
        gene_symbol=observation.gene_symbol,
        contrast_label=observation.contrast_label,
        condition_a=observation.condition_a,
        condition_b=observation.condition_b,
        log2_fold_change=observation.log2_fold_change,
        direction=observation.direction,
        normalized_log2_fold_change=None,
        normalized_direction=None,
        p_value=observation.p_value,
        adjusted_p_value=observation.adjusted_p_value,
        standard_error=observation.standard_error,
        confidence_interval_low=observation.confidence_interval_low,
        confidence_interval_high=observation.confidence_interval_high,
        robustness_score=observation.robustness_score,
        robustness_qc_status=observation.robustness_qc_status,
        significant=observation.significant,
        note=member.note,
    )


def _build_effect_comparison_entry(
    *,
    harmonized_id: str,
    entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    significance_threshold: float,
    low_robustness_threshold: float,
) -> CrossStudyProteinEffectComparisonEntry:
    anchor_condition_a = entries[0].condition_a if entries else None
    anchor_condition_b = entries[0].condition_b if entries else None
    alignment_status, normalized_entries = _normalize_entries_to_anchor(
        entries,
        anchor_condition_a=anchor_condition_a,
        anchor_condition_b=anchor_condition_b,
    )
    significant_entries = tuple(
        entry for entry in normalized_entries if entry.significant
    )
    significant_directions = tuple(
        entry.normalized_direction
        for entry in significant_entries
        if entry.normalized_direction is not None
    )
    conflicting_study_ids = tuple(
        sorted(
            entry.study_id
            for entry in significant_entries
            if entry.normalized_direction
            in {CrossStudyEffectDirection.UP, CrossStudyEffectDirection.DOWN}
        )
    )
    low_robustness_study_ids = tuple(
        sorted(
            entry.study_id
            for entry in normalized_entries
            if _is_low_robustness(
                entry.robustness_score,
                entry.robustness_qc_status,
                threshold=low_robustness_threshold,
            )
        )
    )
    status, note = _comparison_status_and_note(
        normalized_entries,
        alignment_status=alignment_status,
    )
    significant_dirs = {
        direction
        for direction in significant_directions
        if direction in {CrossStudyEffectDirection.UP, CrossStudyEffectDirection.DOWN}
    }
    return CrossStudyProteinEffectComparisonEntry(
        harmonized_id=harmonized_id,
        representative_protein_refs=tuple(
            sorted({entry.representative_protein_ref for entry in normalized_entries})
        ),
        study_ids=tuple(entry.study_id for entry in normalized_entries),
        study_kinds=tuple(entry.study_kind for entry in normalized_entries),
        tested_study_count=len(normalized_entries),
        significant_study_count=len(significant_entries),
        significant_study_ids=tuple(entry.study_id for entry in significant_entries),
        non_significant_study_ids=tuple(
            entry.study_id for entry in normalized_entries if not entry.significant
        ),
        contrast_alignment_status=alignment_status,
        anchor_condition_a=anchor_condition_a,
        anchor_condition_b=anchor_condition_b,
        comparison_status=status,
        replicated_hit=status is CrossStudyEffectComparisonStatus.REPLICATED_HIT,
        study_specific_hit=status
        is CrossStudyEffectComparisonStatus.STUDY_SPECIFIC_HIT,
        conflicting_hit=status is CrossStudyEffectComparisonStatus.CONFLICTING_HIT,
        conflicting_study_ids=(
            conflicting_study_ids if len(significant_dirs) > 1 else ()
        ),
        normalized_significant_directions=tuple(significant_directions),
        min_log2_fold_change=min(
            (entry.log2_fold_change for entry in normalized_entries), default=None
        ),
        max_log2_fold_change=max(
            (entry.log2_fold_change for entry in normalized_entries), default=None
        ),
        median_absolute_log2_fold_change=(
            median(abs(entry.log2_fold_change) for entry in normalized_entries)
            if normalized_entries
            else None
        ),
        min_adjusted_p_value=_minimum_adjusted_p_value(normalized_entries),
        median_robustness_score=_median_robustness_score(normalized_entries),
        low_robustness_study_ids=low_robustness_study_ids,
        note=note,
    )


def _normalize_entries_to_anchor(
    entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    *,
    anchor_condition_a: str | None,
    anchor_condition_b: str | None,
) -> tuple[
    CrossStudyEffectContrastAlignmentStatus,
    tuple[CrossStudyProteinEffectStudyEntry, ...],
]:
    if not entries or anchor_condition_a is None or anchor_condition_b is None:
        return CrossStudyEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS, entries

    normalized_entries: list[CrossStudyProteinEffectStudyEntry] = []
    reversed_seen = False
    for entry in entries:
        if (
            entry.condition_a == anchor_condition_a
            and entry.condition_b == anchor_condition_b
        ):
            normalized_entries.append(
                entry.model_copy(
                    update={
                        "normalized_log2_fold_change": entry.log2_fold_change,
                        "normalized_direction": entry.direction,
                    }
                )
            )
            continue
        if (
            entry.condition_a == anchor_condition_b
            and entry.condition_b == anchor_condition_a
        ):
            reversed_seen = True
            normalized_log2_fold_change = -entry.log2_fold_change
            normalized_entries.append(
                entry.model_copy(
                    update={
                        "normalized_log2_fold_change": normalized_log2_fold_change,
                        "normalized_direction": _direction_from_log2_fold_change(
                            normalized_log2_fold_change
                        ),
                    }
                )
            )
            continue
        return CrossStudyEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS, tuple(
            entry.model_copy(
                update={
                    "normalized_log2_fold_change": None,
                    "normalized_direction": None,
                }
            )
            for entry in entries
        )

    status = (
        CrossStudyEffectContrastAlignmentStatus.REVERSED_ORDER_NORMALIZED
        if reversed_seen
        else CrossStudyEffectContrastAlignmentStatus.SAME_ORDERED_CONTRAST
    )
    return status, tuple(normalized_entries)


def _comparison_status_and_note(
    entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    *,
    alignment_status: CrossStudyEffectContrastAlignmentStatus,
) -> tuple[CrossStudyEffectComparisonStatus, str]:
    if (
        alignment_status
        is CrossStudyEffectContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    ):
        return (
            CrossStudyEffectComparisonStatus.HETEROGENEOUS_CONTRASTS,
            "studies did not compare the same condition pair, so directions were not merged into one replicated or conflicting call",
        )
    significant_entries = tuple(entry for entry in entries if entry.significant)
    if len(significant_entries) >= 2:
        significant_directions = {
            entry.normalized_direction
            for entry in significant_entries
            if entry.normalized_direction
            in {CrossStudyEffectDirection.UP, CrossStudyEffectDirection.DOWN}
        }
        if len(significant_directions) > 1:
            return (
                CrossStudyEffectComparisonStatus.CONFLICTING_HIT,
                "significant studies supported opposite effect directions after contrast alignment",
            )
        if len(significant_directions) == 1:
            return (
                CrossStudyEffectComparisonStatus.REPLICATED_HIT,
                "at least two studies supported the same significant effect direction after contrast alignment",
            )
    if len(significant_entries) == 1 and len(entries) >= 2:
        return (
            CrossStudyEffectComparisonStatus.STUDY_SPECIFIC_HIT,
            "only one study supported a significant effect while the others remained non-significant",
        )
    return (
        CrossStudyEffectComparisonStatus.INSUFFICIENT_SUPPORT,
        "cross-study support was not strong enough to call replication, specificity, or directional conflict",
    )


def _is_significant(
    *,
    adjusted_p_value: float | None,
    p_value: float,
    threshold: float,
) -> bool:
    value = p_value if adjusted_p_value is None else adjusted_p_value
    return value <= threshold


def _is_low_robustness(
    robustness_score: float | None,
    robustness_qc_status: DifferentialResultRobustnessQcStatus | None,
    *,
    threshold: float,
) -> bool:
    if robustness_qc_status is DifferentialResultRobustnessQcStatus.FAIL:
        return True
    if robustness_score is None:
        return False
    return robustness_score < threshold


def _direction_from_log2_fold_change(value: float) -> CrossStudyEffectDirection:
    if value > 0:
        return CrossStudyEffectDirection.UP
    if value < 0:
        return CrossStudyEffectDirection.DOWN
    return CrossStudyEffectDirection.FLAT


def _minimum_adjusted_p_value(
    entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
) -> float | None:
    values = [
        entry.adjusted_p_value if entry.adjusted_p_value is not None else entry.p_value
        for entry in entries
    ]
    return min(values, default=None)


def _median_robustness_score(
    entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
) -> float | None:
    scores = [
        entry.robustness_score
        for entry in entries
        if entry.robustness_score is not None
    ]
    return None if not scores else float(median(scores))


def _render_filtered_effect_tsv(
    report: CrossStudyProteinEffectComparisonReport,
    status: CrossStudyEffectComparisonStatus,
) -> str:
    filtered_report = CrossStudyProteinEffectComparisonReport(
        extracted_effects=report.extracted_effects,
        unsupported_studies=report.unsupported_studies,
        harmonization_report=report.harmonization_report,
        study_entries=report.study_entries,
        comparisons=tuple(
            entry for entry in report.comparisons if entry.comparison_status is status
        ),
        summary=report.summary,
        note=report.note,
    )
    return render_cross_study_effect_comparison_tsv(filtered_report)


def _format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


__all__ = [
    "CrossStudyEffectComparisonStatus",
    "CrossStudyEffectContrastAlignmentStatus",
    "CrossStudyEffectDirection",
    "CrossStudyEffectUnsupportedStudy",
    "CrossStudyProteinEffectComparisonEntry",
    "CrossStudyProteinEffectComparisonReport",
    "CrossStudyProteinEffectComparisonSummary",
    "CrossStudyProteinEffectExtractionReport",
    "CrossStudyProteinEffectExtractionSummary",
    "CrossStudyProteinEffectObservation",
    "CrossStudyProteinStudyInput",
    "CrossStudyProteinEffectStudyEntry",
    "build_cross_study_effect_comparison_report",
    "build_cross_study_effect_comparison_report_from_observations",
    "export_cross_study_conflicting_hit_tsv",
    "export_cross_study_effect_comparison_tsv",
    "export_cross_study_effect_detail_tsv",
    "export_cross_study_replicated_hit_tsv",
    "export_cross_study_study_specific_hit_tsv",
    "extract_cross_study_protein_effect_observations",
    "render_cross_study_conflicting_hit_tsv",
    "render_cross_study_effect_comparison_tsv",
    "render_cross_study_effect_detail_tsv",
    "render_cross_study_replicated_hit_tsv",
    "render_cross_study_study_specific_hit_tsv",
]
