# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering surfaces for targeted assay-QC reports."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.targeted.assay_qc.models import TargetedAssayQcReport
from bijux_proteomics.targeted.transition_coelution import (
    render_targeted_transition_coelution_target_tsv,
    render_targeted_transition_coelution_transition_tsv,
)


def render_targeted_assay_qc_summary_tsv(report: TargetedAssayQcReport) -> str:
    """Render the compact summary for one targeted assay-QC report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "target_count",
            "sample_count",
            "target_qc_entry_count",
            "reliable_target_entry_count",
            "transition_consistency_entry_count",
            "coelution_target_entry_count",
            "flagged_coelution_target_entry_count",
            "transition_coelution_entry_count",
            "coeluting_transition_entry_count",
            "transition_qc_entry_count",
            "passing_transition_qc_entry_count",
            "fragment_ratio_entry_count",
            "fragment_ratio_stability_fragment_entry_count",
            "unstable_fragment_ratio_entry_count",
            "drift_flagged_fragment_ratio_observation_count",
            "retention_time_entry_count",
            "flagged_retention_time_entry_count",
            "replicate_cv_entry_count",
            "flagged_replicate_cv_entry_count",
            "unreliable_target_entry_count",
            "unreliable_target_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.target_count,
            report.summary.sample_count,
            report.summary.target_qc_entry_count,
            report.summary.reliable_target_entry_count,
            report.summary.transition_consistency_entry_count,
            report.summary.coelution_target_entry_count,
            report.summary.flagged_coelution_target_entry_count,
            report.summary.transition_coelution_entry_count,
            report.summary.coeluting_transition_entry_count,
            report.summary.transition_qc_entry_count,
            report.summary.passing_transition_qc_entry_count,
            report.summary.fragment_ratio_entry_count,
            report.summary.fragment_ratio_stability_fragment_entry_count,
            report.summary.unstable_fragment_ratio_entry_count,
            report.summary.drift_flagged_fragment_ratio_observation_count,
            report.summary.retention_time_entry_count,
            report.summary.flagged_retention_time_entry_count,
            report.summary.replicate_cv_entry_count,
            report.summary.flagged_replicate_cv_entry_count,
            report.summary.unreliable_target_entry_count,
            report.summary.unreliable_target_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_targeted_assay_qc_target_tsv(report: TargetedAssayQcReport) -> str:
    """Render sample-resolved target QC rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "condition",
            "expected_transition_count",
            "observed_transition_count",
            "coeluting_transition_count",
            "coeluting_transition_ids",
            "passing_transition_count",
            "passing_transition_ids",
            "failing_transition_ids",
            "passing_total_intensity",
            "mean_retention_time_minutes",
            "reference_retention_time_minutes",
            "absolute_delta_minutes",
            "quality_flag_count",
            "condition_replicate_cv",
            "condition_replicate_cv_flagged",
            "reliability_score",
            "reliable",
            "reliability_reasons",
        ]
    )
    for entry in report.target_qc:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                "" if entry.condition is None else entry.condition,
                entry.expected_transition_count,
                entry.observed_transition_count,
                entry.coeluting_transition_count,
                ";".join(entry.coeluting_transition_ids),
                entry.passing_transition_count,
                ";".join(entry.passing_transition_ids),
                ";".join(entry.failing_transition_ids),
                ""
                if entry.passing_total_intensity is None
                else f"{entry.passing_total_intensity:g}",
                (
                    ""
                    if entry.mean_retention_time_minutes is None
                    else f"{entry.mean_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.reference_retention_time_minutes is None
                    else f"{entry.reference_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.absolute_delta_minutes is None
                    else f"{entry.absolute_delta_minutes:g}"
                ),
                entry.quality_flag_count,
                (
                    ""
                    if entry.condition_replicate_cv is None
                    else f"{entry.condition_replicate_cv:g}"
                ),
                str(entry.condition_replicate_cv_flagged).lower(),
                f"{entry.reliability_score:g}",
                str(entry.reliable).lower(),
                "; ".join(entry.reliability_reasons),
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_transition_tsv(report: TargetedAssayQcReport) -> str:
    """Render sample-level transition consistency as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "detected_transition_count",
            "expected_transition_count",
            "consistency_fraction",
        ]
    )
    for entry in report.transition_consistency:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.detected_transition_count,
                entry.expected_transition_count,
                f"{entry.consistency_fraction:g}",
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_transition_qc_tsv(report: TargetedAssayQcReport) -> str:
    """Render sample-resolved transition QC rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "condition",
            "transition_id",
            "detected",
            "intensity",
            "quality_flag",
            "relative_share",
            "reference_relative_share",
            "absolute_share_delta",
            "ratio_cv",
            "coeluting",
            "coelution_flagged",
            "reference_alignment_flagged",
            "coelution_delta_minutes",
            "reference_delta_minutes",
            "quality_flagged",
            "ratio_flagged",
            "ratio_drift_flagged",
            "ratio_unstable_transition_flagged",
            "passed",
            "failure_reasons",
        ]
    )
    for entry in report.transition_qc:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                "" if entry.condition is None else entry.condition,
                entry.transition_id,
                str(entry.detected).lower(),
                "" if entry.intensity is None else f"{entry.intensity:g}",
                "" if entry.quality_flag is None else entry.quality_flag,
                "" if entry.relative_share is None else f"{entry.relative_share:g}",
                (
                    ""
                    if entry.reference_relative_share is None
                    else f"{entry.reference_relative_share:g}"
                ),
                (
                    ""
                    if entry.absolute_share_delta is None
                    else f"{entry.absolute_share_delta:g}"
                ),
                "" if entry.ratio_cv is None else f"{entry.ratio_cv:g}",
                str(entry.coeluting).lower(),
                str(entry.coelution_flagged).lower(),
                str(entry.reference_alignment_flagged).lower(),
                (
                    ""
                    if entry.coelution_delta_minutes is None
                    else f"{entry.coelution_delta_minutes:g}"
                ),
                (
                    ""
                    if entry.reference_delta_minutes is None
                    else f"{entry.reference_delta_minutes:g}"
                ),
                str(entry.quality_flagged).lower(),
                str(entry.ratio_flagged).lower(),
                str(entry.ratio_drift_flagged).lower(),
                str(entry.ratio_unstable_transition_flagged).lower(),
                str(entry.passed).lower(),
                "; ".join(entry.failure_reasons),
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_fragment_ratio_tsv(report: TargetedAssayQcReport) -> str:
    """Render sample-level fragment-ion ratios as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "transition_id",
            "intensity",
            "total_target_intensity",
            "relative_share",
            "reference_relative_share",
            "absolute_share_delta",
            "ratio_cv",
            "drift_flag",
            "unstable_transition_flagged",
            "flagged",
        ]
    )
    for entry in report.fragment_ratios:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.transition_id,
                f"{entry.intensity:g}",
                f"{entry.total_target_intensity:g}",
                f"{entry.relative_share:g}",
                f"{entry.reference_relative_share:g}",
                f"{entry.absolute_share_delta:g}",
                "" if entry.ratio_cv is None else f"{entry.ratio_cv:g}",
                str(entry.drift_flag).lower(),
                str(entry.unstable_transition_flagged).lower(),
                str(entry.flagged).lower(),
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_coelution_tsv(report: TargetedAssayQcReport) -> str:
    """Render target-level transition coelution review rows as TSV."""

    return render_targeted_transition_coelution_target_tsv(report.transition_coelution)


def render_targeted_assay_qc_transition_coelution_tsv(
    report: TargetedAssayQcReport,
) -> str:
    """Render transition-level coelution review rows as TSV."""

    return render_targeted_transition_coelution_transition_tsv(
        report.transition_coelution
    )


def render_targeted_assay_qc_retention_tsv(report: TargetedAssayQcReport) -> str:
    """Render sample-level retention-time consistency as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "observed_transition_count",
            "mean_retention_time_minutes",
            "reference_retention_time_minutes",
            "absolute_delta_minutes",
            "flagged",
        ]
    )
    for entry in report.retention_time_consistency:
        writer.writerow(
            [
                entry.target_id,
                entry.sample_id,
                entry.observed_transition_count,
                ""
                if entry.mean_retention_time_minutes is None
                else f"{entry.mean_retention_time_minutes:g}",
                (
                    ""
                    if entry.reference_retention_time_minutes is None
                    else f"{entry.reference_retention_time_minutes:g}"
                ),
                (
                    ""
                    if entry.absolute_delta_minutes is None
                    else f"{entry.absolute_delta_minutes:g}"
                ),
                str(entry.flagged).lower(),
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_replicate_cv_tsv(report: TargetedAssayQcReport) -> str:
    """Render condition-level replicate CV as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "condition",
            "replicate_count",
            "detected_replicate_count",
            "mean_intensity",
            "coefficient_of_variation",
            "flagged",
        ]
    )
    for entry in report.replicate_cv:
        writer.writerow(
            [
                entry.target_id,
                entry.condition,
                entry.replicate_count,
                entry.detected_replicate_count,
                "" if entry.mean_intensity is None else f"{entry.mean_intensity:g}",
                (
                    ""
                    if entry.coefficient_of_variation is None
                    else f"{entry.coefficient_of_variation:g}"
                ),
                str(entry.flagged).lower(),
            ]
        )
    return buffer.getvalue()


def render_targeted_assay_qc_unreliable_tsv(report: TargetedAssayQcReport) -> str:
    """Render explicit unreliable-target entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "target_id",
            "sample_id",
            "condition",
            "flagged_transition_ids",
            "quality_flags",
            "reasons",
        ]
    )
    for entry in report.unreliable_targets:
        writer.writerow(
            [
                entry.target_id,
                "" if entry.sample_id is None else entry.sample_id,
                "" if entry.condition is None else entry.condition,
                ";".join(entry.flagged_transition_ids),
                ";".join(entry.quality_flags),
                "; ".join(entry.reasons),
            ]
        )
    return buffer.getvalue()


__all__ = [
    "render_targeted_assay_qc_coelution_tsv",
    "render_targeted_assay_qc_fragment_ratio_tsv",
    "render_targeted_assay_qc_replicate_cv_tsv",
    "render_targeted_assay_qc_retention_tsv",
    "render_targeted_assay_qc_summary_tsv",
    "render_targeted_assay_qc_target_tsv",
    "render_targeted_assay_qc_transition_coelution_tsv",
    "render_targeted_assay_qc_transition_qc_tsv",
    "render_targeted_assay_qc_transition_tsv",
    "render_targeted_assay_qc_unreliable_tsv",
]
