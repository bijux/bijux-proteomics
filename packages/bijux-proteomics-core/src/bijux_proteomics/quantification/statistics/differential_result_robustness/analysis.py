# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Report assembly for differential-result robustness surfaces."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
    TimeCourseDifferentialReport,
)
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import (
    LabelFreeQuantTable,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    ReplicateAndBatchQcReport,
)
from bijux_proteomics.quantification.provenance.replicate_qc import (
    build_replicate_and_batch_qc_report,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.entry_builders import (
    build_pairwise_robustness_entry,
    build_robustness_report,
    build_time_course_robustness_entry,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.models import (
    DifferentialResultRobustnessAnalysisKind,
    DifferentialResultRobustnessReport,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.scoring_policy import (
    qc_status_components,
)


def build_differential_abundance_robustness_report(
    report: DifferentialAbundanceReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialResultRobustnessReport:
    """Score each pairwise differential result beyond p-value ranking alone."""

    active_qc = replicate_qc_report or build_replicate_and_batch_qc_report(
        table,
        design_entries=design_entries,
    )
    sample_ids_by_condition = _sample_ids_by_condition(table, design_entries)
    lookup = _matrix_value_index(table)
    qc_status, qc_score, qc_reasons = qc_status_components(active_qc)
    entries = tuple(
        sorted(
            (
                build_pairwise_robustness_entry(
                    entry=entry,
                    table=table,
                    lookup=lookup,
                    sample_ids_a=sample_ids_by_condition.get(entry.condition_a, ()),
                    sample_ids_b=sample_ids_by_condition.get(entry.condition_b, ()),
                    qc_status=qc_status,
                    qc_score=qc_score,
                    qc_reasons=qc_reasons,
                )
                for entry in report.entries
            ),
            key=lambda entry: (
                entry.entity_id,
                entry.primary_condition,
                entry.comparison_condition or "",
            ),
        )
    )
    return build_robustness_report(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TWO_CONDITION,
        entries=entries,
    )


def annotate_differential_abundance_report_robustness(
    report: DifferentialAbundanceReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialAbundanceReport:
    """Attach owned robustness fields to pairwise differential-result rows."""

    robustness_report = build_differential_abundance_robustness_report(
        report,
        table,
        design_entries,
        replicate_qc_report=replicate_qc_report,
    )
    robustness_by_key = {
        (entry.entity_id, entry.primary_condition, entry.comparison_condition): entry
        for entry in robustness_report.entries
    }
    entries = tuple(
        result_entry.model_copy(
            update={
                "robustness_score": robustness_entry.robustness_score,
                "robustness_qc_status": robustness_entry.qc_status,
                "robustness_reason_codes": robustness_entry.reason_codes,
                "robustness_note": robustness_entry.note,
            }
        )
        for result_entry in report.entries
        if (
            robustness_entry := robustness_by_key[
                (
                    result_entry.entity_id,
                    result_entry.condition_a,
                    result_entry.condition_b,
                )
            ]
        )
    )
    return report.model_copy(update={"entries": entries})


def build_time_course_differential_robustness_report(
    report: TimeCourseDifferentialReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> DifferentialResultRobustnessReport:
    """Score each ordered-timepoint differential result beyond significance alone."""

    active_qc = replicate_qc_report or build_replicate_and_batch_qc_report(
        table,
        design_entries=design_entries,
    )
    sample_ids_by_condition = _sample_ids_by_condition(table, design_entries)
    lookup = _matrix_value_index(table)
    qc_status, qc_score, qc_reasons = qc_status_components(active_qc)
    entries = tuple(
        sorted(
            (
                build_time_course_robustness_entry(
                    entry=entry,
                    ordered_timepoint_count=max(len(report.ordered_timepoints), 1),
                    table=table,
                    lookup=lookup,
                    primary_sample_ids=sample_ids_by_condition.get(entry.condition, ()),
                    comparison_sample_ids=sample_ids_by_condition.get(
                        entry.reference_condition, ()
                    ),
                    qc_status=qc_status,
                    qc_score=qc_score,
                    qc_reasons=qc_reasons,
                )
                for entry in report.entries
            ),
            key=lambda entry: (
                entry.entity_id,
                entry.primary_condition,
                entry.comparison_condition or "",
            ),
        )
    )
    return build_robustness_report(
        analysis_kind=DifferentialResultRobustnessAnalysisKind.TIME_COURSE,
        entries=entries,
    )


def annotate_time_course_differential_report_robustness(
    report: TimeCourseDifferentialReport,
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
) -> TimeCourseDifferentialReport:
    """Attach owned robustness fields to ordered-timepoint differential rows."""

    robustness_report = build_time_course_differential_robustness_report(
        report,
        table,
        design_entries,
        replicate_qc_report=replicate_qc_report,
    )
    robustness_by_key = {
        (entry.entity_id, entry.primary_condition, entry.comparison_condition): entry
        for entry in robustness_report.entries
    }
    entries = tuple(
        result_entry.model_copy(
            update={
                "robustness_score": robustness_entry.robustness_score,
                "robustness_qc_status": robustness_entry.qc_status,
                "robustness_reason_codes": robustness_entry.reason_codes,
                "robustness_note": robustness_entry.note,
            }
        )
        for result_entry in report.entries
        if (
            robustness_entry := robustness_by_key[
                (
                    result_entry.entity_id,
                    result_entry.condition,
                    result_entry.reference_condition,
                )
            ]
        )
    )
    return report.model_copy(update={"entries": entries})


def _sample_ids_by_condition(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, tuple[str, ...]]:
    condition_by_sample = _condition_lookup(design_entries)
    sample_ids_by_condition: dict[str, tuple[str, ...]] = {}
    for condition in sorted(
        {condition for condition in condition_by_sample.values() if condition}
    ):
        sample_ids_by_condition[condition] = tuple(
            sample_id
            for sample_id in table.sample_ids
            if condition_by_sample.get(sample_id) == condition
        )
    return sample_ids_by_condition


__all__ = [
    "annotate_differential_abundance_report_robustness",
    "annotate_time_course_differential_report_robustness",
    "build_differential_abundance_robustness_report",
    "build_time_course_differential_robustness_report",
]
