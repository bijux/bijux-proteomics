# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-study evidence cards over public dataset comparison outputs."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.semantic_ids import build_cross_study_card_id
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectComparisonStatus,
    CrossStudyProteinEffectComparisonEntry,
    CrossStudyProteinEffectStudyEntry,
)
from bijux_proteomics.workflow.cross_study_meta_analysis import (
    CrossStudyMetaAnalysisEntry,
    CrossStudyMetaAnalysisRejectedEntry,
)
from bijux_proteomics.workflow.cross_study_pathway_comparison import (
    CrossStudyPathwayComparisonEntry,
    CrossStudyPathwayComparisonStatus,
    CrossStudyPathwayStudyEntry,
)
from bijux_proteomics.workflow.public_dataset_comparison import (
    PublicDatasetComparisonDatasetSummary,
    PublicDatasetComparisonDatasetStatus,
    PublicDatasetComparisonReport,
)
from bijux_proteomics_foundation import JsonModel


class CrossStudyEvidenceSubjectKind(StrEnum):
    """Stable subject families represented by cross-study evidence cards."""

    PROTEIN = "protein"
    PATHWAY = "pathway"


class CrossStudyEvidenceCardStatus(StrEnum):
    """Stable cross-dataset evidence conclusions shown on one card."""

    CONSISTENT_REPLICATION = "consistent_replication"
    CONFLICTING_DATASETS = "conflicting_datasets"
    DATASET_SPECIFIC_SIGNAL = "dataset_specific_signal"
    HETEROGENEOUS_COMPARISON = "heterogeneous_comparison"
    INSUFFICIENT_CROSS_DATASET_SUPPORT = "insufficient_cross_dataset_support"


class CrossStudyEvidenceDatasetState(StrEnum):
    """Stable per-dataset evidence states preserved on one cross-study card."""

    POSITIVE_SIGNAL = "positive_signal"
    NEGATIVE_SIGNAL = "negative_signal"
    SIGNIFICANT_SIGNAL = "significant_signal"
    NON_SIGNIFICANT = "non_significant"
    NOT_OBSERVED = "not_observed"
    COMPARISON_UNSUPPORTED = "comparison_unsupported"
    DATASET_FAILED = "dataset_failed"


class CrossStudyEvidenceCardDatasetEntry(JsonModel):
    """One per-dataset evidence block nested under one cross-study card."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    search_engine: str = Field(..., min_length=1)
    dataset_status: PublicDatasetComparisonDatasetStatus
    dataset_state: CrossStudyEvidenceDatasetState
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    direction: str | None = None
    significant: bool | None = None
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class CrossStudyEvidenceCardEntry(JsonModel):
    """One protein- or pathway-level cross-study evidence card."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    subject_kind: CrossStudyEvidenceSubjectKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    final_status: CrossStudyEvidenceCardStatus
    dataset_count: int = Field(..., ge=0)
    observed_dataset_count: int = Field(..., ge=0)
    positive_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    negative_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    significant_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    non_significant_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    failed_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    unobserved_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    combined_effect_size: float | None = None
    combined_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    heterogeneity_i_squared: float | None = Field(default=None, ge=0.0, le=1.0)
    pathway_coverage_range: float | None = Field(default=None, ge=0.0, le=1.0)
    dataset_entries: tuple[CrossStudyEvidenceCardDatasetEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class CrossStudyEvidenceCardSummary(JsonModel):
    """Compact summary over one cross-study evidence card pass."""

    model_config = ConfigDict(extra="forbid")

    card_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    pathway_card_count: int = Field(..., ge=0)
    consistent_replication_count: int = Field(..., ge=0)
    conflicting_dataset_count: int = Field(..., ge=0)
    dataset_specific_count: int = Field(..., ge=0)
    heterogeneous_comparison_count: int = Field(..., ge=0)
    insufficient_support_count: int = Field(..., ge=0)
    failed_dataset_reference_count: int = Field(..., ge=0)


class CrossStudyEvidenceCardReport(JsonModel):
    """Owned cross-study evidence cards over public dataset comparison outputs."""

    model_config = ConfigDict(extra="forbid")

    public_dataset_report: PublicDatasetComparisonReport
    cards: tuple[CrossStudyEvidenceCardEntry, ...] = Field(default_factory=tuple)
    summary: CrossStudyEvidenceCardSummary
    note: str = Field(..., min_length=1)


def build_cross_study_evidence_card_report(
    public_dataset_report: PublicDatasetComparisonReport,
) -> CrossStudyEvidenceCardReport:
    """Build protein and pathway evidence cards from one public dataset comparison."""

    dataset_by_id = {
        entry.dataset_id: entry for entry in public_dataset_report.dataset_summaries
    }
    failure_entries_by_dataset: dict[str, list[str]] = {}
    for failure_entry in public_dataset_report.failure_entries:
        failure_entries_by_dataset.setdefault(failure_entry.dataset_id, []).append(
            f"{failure_entry.failure_kind}: {failure_entry.subject}"
        )

    cards: list[CrossStudyEvidenceCardEntry] = []
    effect_report = public_dataset_report.effect_comparison_report
    meta_report = public_dataset_report.meta_analysis_report
    pathway_report = public_dataset_report.pathway_comparison_report

    if effect_report is not None:
        study_entries_by_harmonized_id: dict[str, list[CrossStudyProteinEffectStudyEntry]] = {}
        for entry in effect_report.study_entries:
            study_entries_by_harmonized_id.setdefault(entry.harmonized_id, []).append(entry)
        meta_entries_by_harmonized_id = (
            {}
            if meta_report is None
            else {entry.harmonized_id: entry for entry in meta_report.combined_entries}
        )
        meta_rejections_by_harmonized_id = (
            {}
            if meta_report is None
            else {entry.harmonized_id: entry for entry in meta_report.rejected_entries}
        )
        effect_unsupported_ids = {entry.study_id for entry in effect_report.unsupported_studies}
        for comparison in effect_report.comparisons:
            cards.append(
                _build_protein_card(
                    comparison=comparison,
                    study_entries=tuple(
                        sorted(
                            study_entries_by_harmonized_id.get(comparison.harmonized_id, []),
                            key=lambda entry: entry.study_id,
                        )
                    ),
                    meta_entry=meta_entries_by_harmonized_id.get(comparison.harmonized_id),
                    meta_rejection=meta_rejections_by_harmonized_id.get(comparison.harmonized_id),
                    dataset_by_id=dataset_by_id,
                    failure_entries_by_dataset=failure_entries_by_dataset,
                    unsupported_dataset_ids=effect_unsupported_ids,
                )
            )

    if pathway_report is not None:
        study_entries_by_comparison_id: dict[str, list[CrossStudyPathwayStudyEntry]] = {}
        for entry in pathway_report.study_entries:
            study_entries_by_comparison_id.setdefault(entry.comparison_id, []).append(entry)
        pathway_unsupported_ids = {
            entry.study_id for entry in pathway_report.unsupported_studies
        }
        for comparison in pathway_report.comparisons:
            cards.append(
                _build_pathway_card(
                    comparison=comparison,
                    study_entries=tuple(
                        sorted(
                            study_entries_by_comparison_id.get(comparison.comparison_id, []),
                            key=lambda entry: entry.study_id,
                        )
                    ),
                    dataset_by_id=dataset_by_id,
                    failure_entries_by_dataset=failure_entries_by_dataset,
                    unsupported_dataset_ids=pathway_unsupported_ids,
                )
            )

    ordered_cards = tuple(
        sorted(
            cards,
            key=lambda entry: (entry.subject_kind.value, entry.subject_id, entry.card_id),
        )
    )
    summary = CrossStudyEvidenceCardSummary(
        card_count=len(ordered_cards),
        protein_card_count=sum(
            entry.subject_kind is CrossStudyEvidenceSubjectKind.PROTEIN
            for entry in ordered_cards
        ),
        pathway_card_count=sum(
            entry.subject_kind is CrossStudyEvidenceSubjectKind.PATHWAY
            for entry in ordered_cards
        ),
        consistent_replication_count=sum(
            entry.final_status is CrossStudyEvidenceCardStatus.CONSISTENT_REPLICATION
            for entry in ordered_cards
        ),
        conflicting_dataset_count=sum(
            entry.final_status is CrossStudyEvidenceCardStatus.CONFLICTING_DATASETS
            for entry in ordered_cards
        ),
        dataset_specific_count=sum(
            entry.final_status is CrossStudyEvidenceCardStatus.DATASET_SPECIFIC_SIGNAL
            for entry in ordered_cards
        ),
        heterogeneous_comparison_count=sum(
            entry.final_status is CrossStudyEvidenceCardStatus.HETEROGENEOUS_COMPARISON
            for entry in ordered_cards
        ),
        insufficient_support_count=sum(
            entry.final_status
            is CrossStudyEvidenceCardStatus.INSUFFICIENT_CROSS_DATASET_SUPPORT
            for entry in ordered_cards
        ),
        failed_dataset_reference_count=sum(
            len(entry.failed_dataset_ids) for entry in ordered_cards
        ),
    )
    return CrossStudyEvidenceCardReport(
        public_dataset_report=public_dataset_report,
        cards=ordered_cards,
        summary=summary,
        note=(
            "cross-study evidence cards preserve one structured protein or pathway "
            "subject per comparison group and keep per-dataset support, conflict, "
            "and failure visibility instead of collapsing everything into one merged row"
        ),
    )


def build_public_dataset_evidence_card_report(
    benchmark_root: Path,
    *,
    run_output_root: Path,
) -> CrossStudyEvidenceCardReport:
    """Run public dataset comparison first, then build cross-study evidence cards."""

    from bijux_proteomics.workflow.public_dataset_comparison import (
        build_public_dataset_comparison_report,
    )

    return build_cross_study_evidence_card_report(
        build_public_dataset_comparison_report(
            benchmark_root,
            run_output_root=run_output_root,
        )
    )


def render_cross_study_evidence_card_summary_tsv(
    report: CrossStudyEvidenceCardReport,
) -> str:
    """Render one-row cross-study evidence card summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "card_count",
            "protein_card_count",
            "pathway_card_count",
            "consistent_replication_count",
            "conflicting_dataset_count",
            "dataset_specific_count",
            "heterogeneous_comparison_count",
            "insufficient_support_count",
            "failed_dataset_reference_count",
        ]
    )
    writer.writerow(
        [
            report.summary.card_count,
            report.summary.protein_card_count,
            report.summary.pathway_card_count,
            report.summary.consistent_replication_count,
            report.summary.conflicting_dataset_count,
            report.summary.dataset_specific_count,
            report.summary.heterogeneous_comparison_count,
            report.summary.insufficient_support_count,
            report.summary.failed_dataset_reference_count,
        ]
    )
    return buffer.getvalue()


def render_cross_study_evidence_card_tsv(report: CrossStudyEvidenceCardReport) -> str:
    """Render flattened cross-study evidence cards as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "card_id",
            "subject_kind",
            "subject_id",
            "subject_label",
            "final_status",
            "dataset_count",
            "observed_dataset_count",
            "positive_dataset_ids",
            "negative_dataset_ids",
            "significant_dataset_ids",
            "non_significant_dataset_ids",
            "unsupported_dataset_ids",
            "failed_dataset_ids",
            "unobserved_dataset_ids",
            "combined_effect_size",
            "combined_adjusted_p_value",
            "heterogeneity_i_squared",
            "pathway_coverage_range",
            "note",
        ]
    )
    for entry in report.cards:
        writer.writerow(
            [
                entry.card_id,
                entry.subject_kind.value,
                entry.subject_id,
                entry.subject_label,
                entry.final_status.value,
                entry.dataset_count,
                entry.observed_dataset_count,
                ";".join(entry.positive_dataset_ids),
                ";".join(entry.negative_dataset_ids),
                ";".join(entry.significant_dataset_ids),
                ";".join(entry.non_significant_dataset_ids),
                ";".join(entry.unsupported_dataset_ids),
                ";".join(entry.failed_dataset_ids),
                ";".join(entry.unobserved_dataset_ids),
                _format_float(entry.combined_effect_size),
                _format_float(entry.combined_adjusted_p_value),
                _format_float(entry.heterogeneity_i_squared),
                _format_float(entry.pathway_coverage_range),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_cross_study_evidence_dataset_tsv(report: CrossStudyEvidenceCardReport) -> str:
    """Render per-dataset evidence nested under every card as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "card_id",
            "dataset_id",
            "accession",
            "search_engine",
            "dataset_status",
            "dataset_state",
            "condition_a",
            "condition_b",
            "direction",
            "significant",
            "effect_size",
            "adjusted_p_value",
            "coverage_fraction",
            "note",
        ]
    )
    for card in report.cards:
        for entry in card.dataset_entries:
            writer.writerow(
                [
                    entry.card_id,
                    entry.dataset_id,
                    entry.accession,
                    entry.search_engine,
                    entry.dataset_status.value,
                    entry.dataset_state.value,
                    entry.condition_a,
                    entry.condition_b,
                    "" if entry.direction is None else entry.direction,
                    (
                        ""
                        if entry.significant is None
                        else str(entry.significant).lower()
                    ),
                    _format_float(entry.effect_size),
                    _format_float(entry.adjusted_p_value),
                    _format_float(entry.coverage_fraction),
                    entry.note,
                ]
            )
    return buffer.getvalue()


def _build_protein_card(
    *,
    comparison: CrossStudyProteinEffectComparisonEntry,
    study_entries: tuple[CrossStudyProteinEffectStudyEntry, ...],
    meta_entry: CrossStudyMetaAnalysisEntry | None,
    meta_rejection: CrossStudyMetaAnalysisRejectedEntry | None,
    dataset_by_id: dict[str, PublicDatasetComparisonDatasetSummary],
    failure_entries_by_dataset: dict[str, list[str]],
    unsupported_dataset_ids: set[str],
) -> CrossStudyEvidenceCardEntry:
    card_id = _card_id(CrossStudyEvidenceSubjectKind.PROTEIN, comparison.harmonized_id)
    entries_by_dataset = {entry.study_id: entry for entry in study_entries}
    dataset_entries = tuple(
        _protein_dataset_entry(
            card_id=card_id,
            dataset_summary=dataset_summary,
            study_entry=entries_by_dataset.get(dataset_id),
            failure_notes=failure_entries_by_dataset.get(dataset_id, ()),
            comparison_unsupported=dataset_id in unsupported_dataset_ids,
        )
        for dataset_id, dataset_summary in sorted(dataset_by_id.items())
    )
    positive_dataset_ids, negative_dataset_ids, significant_dataset_ids = (
        _directional_dataset_sets(dataset_entries)
    )
    non_significant_dataset_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.NON_SIGNIFICANT
    )
    unsupported_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.COMPARISON_UNSUPPORTED
    )
    failed_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.DATASET_FAILED
    )
    unobserved_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.NOT_OBSERVED
    )
    meta_note = (
        ""
        if meta_rejection is None
        else f" meta-analysis unavailable: {meta_rejection.rejection_reason.value}."
    )
    return CrossStudyEvidenceCardEntry(
        card_id=card_id,
        subject_kind=CrossStudyEvidenceSubjectKind.PROTEIN,
        subject_id=comparison.harmonized_id,
        subject_label="; ".join(comparison.representative_protein_refs),
        final_status=_protein_card_status(comparison.comparison_status),
        dataset_count=len(dataset_entries),
        observed_dataset_count=len(study_entries),
        positive_dataset_ids=positive_dataset_ids,
        negative_dataset_ids=negative_dataset_ids,
        significant_dataset_ids=significant_dataset_ids,
        non_significant_dataset_ids=non_significant_dataset_ids,
        unsupported_dataset_ids=unsupported_ids,
        failed_dataset_ids=failed_ids,
        unobserved_dataset_ids=unobserved_ids,
        combined_effect_size=(
            None if meta_entry is None else meta_entry.combined_log2_fold_change
        ),
        combined_adjusted_p_value=(
            None if meta_entry is None else meta_entry.combined_adjusted_p_value
        ),
        heterogeneity_i_squared=(
            None if meta_entry is None else meta_entry.heterogeneity_i_squared
        ),
        pathway_coverage_range=None,
        dataset_entries=dataset_entries,
        note=f"{comparison.note}.{meta_note}".strip(),
    )


def _build_pathway_card(
    *,
    comparison: CrossStudyPathwayComparisonEntry,
    study_entries: tuple[CrossStudyPathwayStudyEntry, ...],
    dataset_by_id: dict[str, PublicDatasetComparisonDatasetSummary],
    failure_entries_by_dataset: dict[str, list[str]],
    unsupported_dataset_ids: set[str],
) -> CrossStudyEvidenceCardEntry:
    card_id = _card_id(CrossStudyEvidenceSubjectKind.PATHWAY, comparison.comparison_id)
    entries_by_dataset = {entry.study_id: entry for entry in study_entries}
    dataset_entries = tuple(
        _pathway_dataset_entry(
            card_id=card_id,
            dataset_summary=dataset_summary,
            study_entry=entries_by_dataset.get(dataset_id),
            failure_notes=failure_entries_by_dataset.get(dataset_id, ()),
            comparison_unsupported=dataset_id in unsupported_dataset_ids,
        )
        for dataset_id, dataset_summary in sorted(dataset_by_id.items())
    )
    positive_dataset_ids, negative_dataset_ids, significant_dataset_ids = (
        _directional_dataset_sets(dataset_entries)
    )
    non_significant_dataset_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.NON_SIGNIFICANT
    )
    unsupported_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.COMPARISON_UNSUPPORTED
    )
    failed_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.DATASET_FAILED
    )
    unobserved_ids = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.NOT_OBSERVED
    )
    return CrossStudyEvidenceCardEntry(
        card_id=card_id,
        subject_kind=CrossStudyEvidenceSubjectKind.PATHWAY,
        subject_id=comparison.pathway_id,
        subject_label=comparison.pathway_name or comparison.pathway_id,
        final_status=_pathway_card_status(comparison.comparison_status),
        dataset_count=len(dataset_entries),
        observed_dataset_count=len(study_entries),
        positive_dataset_ids=positive_dataset_ids,
        negative_dataset_ids=negative_dataset_ids,
        significant_dataset_ids=significant_dataset_ids,
        non_significant_dataset_ids=non_significant_dataset_ids,
        unsupported_dataset_ids=unsupported_ids,
        failed_dataset_ids=failed_ids,
        unobserved_dataset_ids=unobserved_ids,
        combined_effect_size=None,
        combined_adjusted_p_value=comparison.minimum_adjusted_p_value,
        heterogeneity_i_squared=None,
        pathway_coverage_range=comparison.coverage_fraction_range,
        dataset_entries=dataset_entries,
        note=comparison.note,
    )


def _protein_dataset_entry(
    *,
    card_id: str,
    dataset_summary: PublicDatasetComparisonDatasetSummary,
    study_entry: CrossStudyProteinEffectStudyEntry | None,
    failure_notes: tuple[str, ...] | list[str],
    comparison_unsupported: bool,
) -> CrossStudyEvidenceCardDatasetEntry:
    if dataset_summary.status is PublicDatasetComparisonDatasetStatus.FAILED:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.DATASET_FAILED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="; ".join(failure_notes) or dataset_summary.note,
        )
    if comparison_unsupported:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.COMPARISON_UNSUPPORTED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="dataset result could not contribute governed protein effect comparison",
        )
    if study_entry is None:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.NOT_OBSERVED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="subject was not observed on the harmonized protein effect surface for this dataset",
        )
    direction = (
        study_entry.normalized_direction.value
        if study_entry.normalized_direction is not None
        else study_entry.direction.value
    )
    state = _signal_state(
        significant=study_entry.significant,
        direction=direction,
    )
    return CrossStudyEvidenceCardDatasetEntry(
        card_id=card_id,
        dataset_id=dataset_summary.dataset_id,
        accession=dataset_summary.accession,
        search_engine=dataset_summary.search_engine,
        dataset_status=dataset_summary.status,
        dataset_state=state,
        condition_a=study_entry.condition_a,
        condition_b=study_entry.condition_b,
        direction=direction,
        significant=study_entry.significant,
        effect_size=(
            study_entry.normalized_log2_fold_change
            if study_entry.normalized_log2_fold_change is not None
            else study_entry.log2_fold_change
        ),
        adjusted_p_value=study_entry.adjusted_p_value,
        note=study_entry.note,
    )


def _pathway_dataset_entry(
    *,
    card_id: str,
    dataset_summary: PublicDatasetComparisonDatasetSummary,
    study_entry: CrossStudyPathwayStudyEntry | None,
    failure_notes: tuple[str, ...] | list[str],
    comparison_unsupported: bool,
) -> CrossStudyEvidenceCardDatasetEntry:
    if dataset_summary.status is PublicDatasetComparisonDatasetStatus.FAILED:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.DATASET_FAILED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="; ".join(failure_notes) or dataset_summary.note,
        )
    if comparison_unsupported:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.COMPARISON_UNSUPPORTED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="dataset result could not contribute governed pathway comparison",
        )
    if study_entry is None:
        return CrossStudyEvidenceCardDatasetEntry(
            card_id=card_id,
            dataset_id=dataset_summary.dataset_id,
            accession=dataset_summary.accession,
            search_engine=dataset_summary.search_engine,
            dataset_status=dataset_summary.status,
            dataset_state=CrossStudyEvidenceDatasetState.NOT_OBSERVED,
            condition_a=dataset_summary.condition_a,
            condition_b=dataset_summary.condition_b,
            note="subject was not observed on the governed pathway comparison surface for this dataset",
        )
    direction = (
        study_entry.normalized_direction.value
        if study_entry.normalized_direction is not None
        else (None if study_entry.direction is None else study_entry.direction.value)
    )
    effect_size = (
        study_entry.normalized_activity_score_delta
        if study_entry.normalized_activity_score_delta is not None
        else study_entry.enrichment_ratio
    )
    state = _signal_state(
        significant=study_entry.significant,
        direction=direction,
    )
    return CrossStudyEvidenceCardDatasetEntry(
        card_id=card_id,
        dataset_id=dataset_summary.dataset_id,
        accession=dataset_summary.accession,
        search_engine=dataset_summary.search_engine,
        dataset_status=dataset_summary.status,
        dataset_state=state,
        condition_a=study_entry.condition_a or dataset_summary.condition_a,
        condition_b=study_entry.condition_b or dataset_summary.condition_b,
        direction=direction,
        significant=study_entry.significant,
        effect_size=effect_size,
        adjusted_p_value=study_entry.adjusted_p_value,
        coverage_fraction=study_entry.coverage_fraction,
        note=study_entry.note,
    )


def _signal_state(
    *,
    significant: bool,
    direction: str | None,
) -> CrossStudyEvidenceDatasetState:
    if not significant:
        return CrossStudyEvidenceDatasetState.NON_SIGNIFICANT
    if direction == "up":
        return CrossStudyEvidenceDatasetState.POSITIVE_SIGNAL
    if direction == "down":
        return CrossStudyEvidenceDatasetState.NEGATIVE_SIGNAL
    return CrossStudyEvidenceDatasetState.SIGNIFICANT_SIGNAL


def _directional_dataset_sets(
    dataset_entries: tuple[CrossStudyEvidenceCardDatasetEntry, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    positive = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.POSITIVE_SIGNAL
    )
    negative = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state is CrossStudyEvidenceDatasetState.NEGATIVE_SIGNAL
    )
    significant = tuple(
        entry.dataset_id
        for entry in dataset_entries
        if entry.dataset_state
        in {
            CrossStudyEvidenceDatasetState.POSITIVE_SIGNAL,
            CrossStudyEvidenceDatasetState.NEGATIVE_SIGNAL,
            CrossStudyEvidenceDatasetState.SIGNIFICANT_SIGNAL,
        }
    )
    return positive, negative, significant


def _protein_card_status(
    status: CrossStudyEffectComparisonStatus,
) -> CrossStudyEvidenceCardStatus:
    if status is CrossStudyEffectComparisonStatus.REPLICATED_HIT:
        return CrossStudyEvidenceCardStatus.CONSISTENT_REPLICATION
    if status is CrossStudyEffectComparisonStatus.CONFLICTING_HIT:
        return CrossStudyEvidenceCardStatus.CONFLICTING_DATASETS
    if status is CrossStudyEffectComparisonStatus.STUDY_SPECIFIC_HIT:
        return CrossStudyEvidenceCardStatus.DATASET_SPECIFIC_SIGNAL
    if status is CrossStudyEffectComparisonStatus.HETEROGENEOUS_CONTRASTS:
        return CrossStudyEvidenceCardStatus.HETEROGENEOUS_COMPARISON
    return CrossStudyEvidenceCardStatus.INSUFFICIENT_CROSS_DATASET_SUPPORT


def _pathway_card_status(
    status: CrossStudyPathwayComparisonStatus,
) -> CrossStudyEvidenceCardStatus:
    if status is CrossStudyPathwayComparisonStatus.SHARED_SIGNAL:
        return CrossStudyEvidenceCardStatus.CONSISTENT_REPLICATION
    if status is CrossStudyPathwayComparisonStatus.OPPOSITE_SIGNAL:
        return CrossStudyEvidenceCardStatus.CONFLICTING_DATASETS
    if status is CrossStudyPathwayComparisonStatus.STUDY_SPECIFIC_SIGNAL:
        return CrossStudyEvidenceCardStatus.DATASET_SPECIFIC_SIGNAL
    if status is CrossStudyPathwayComparisonStatus.HETEROGENEOUS_CONTRASTS:
        return CrossStudyEvidenceCardStatus.HETEROGENEOUS_COMPARISON
    return CrossStudyEvidenceCardStatus.INSUFFICIENT_CROSS_DATASET_SUPPORT


def _card_id(subject_kind: CrossStudyEvidenceSubjectKind, subject_id: str) -> str:
    return build_cross_study_card_id(subject_kind, subject_id)


def _format_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


__all__ = [
    "CrossStudyEvidenceCardDatasetEntry",
    "CrossStudyEvidenceCardEntry",
    "CrossStudyEvidenceCardReport",
    "CrossStudyEvidenceCardStatus",
    "CrossStudyEvidenceCardSummary",
    "CrossStudyEvidenceDatasetState",
    "CrossStudyEvidenceSubjectKind",
    "build_cross_study_evidence_card_report",
    "build_public_dataset_evidence_card_report",
    "render_cross_study_evidence_card_summary_tsv",
    "render_cross_study_evidence_card_tsv",
    "render_cross_study_evidence_dataset_tsv",
]
