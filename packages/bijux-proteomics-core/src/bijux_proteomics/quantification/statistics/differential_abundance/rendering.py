# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable rendering surfaces for differential abundance reports."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
    MultiConditionDifferentialAbundanceReport,
)


def render_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one differential-abundance report as a stable TSV table."""

    return _render_differential_rows((report,))


def render_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
) -> str:
    """Render one paired-design broken-pair ledger as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "condition_a",
            "condition_b",
            "pair_id",
            "sample_ids_a",
            "sample_ids_b",
            "reason_code",
            "detail",
        ]
    )
    for entry in report.broken_pairs:
        writer.writerow(
            [
                entry.condition_a,
                entry.condition_b,
                entry.pair_id or "",
                ";".join(entry.sample_ids_a),
                ";".join(entry.sample_ids_b),
                entry.reason_code,
                entry.detail,
            ]
        )
    return buffer.getvalue()


def export_differential_broken_pairs_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one paired-design broken-pair ledger to a stable TSV artifact."""

    write_output_table_tsv(path, render_differential_broken_pairs_tsv(report))


def export_differential_abundance_tsv(
    report: DifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write one differential-abundance report to a stable TSV artifact."""

    write_output_table_tsv(path, render_differential_abundance_tsv(report))


def render_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
) -> str:
    """Render a multi-condition DA collection as one flattened TSV table."""

    return _render_differential_rows(report.reports)


def export_multi_condition_differential_abundance_tsv(
    report: MultiConditionDifferentialAbundanceReport,
    path: Path,
) -> None:
    """Write a multi-condition DA collection to one flattened TSV artifact."""

    write_output_table_tsv(
        path, render_multi_condition_differential_abundance_tsv(report)
    )


def _render_differential_rows(
    reports: tuple[DifferentialAbundanceReport, ...],
) -> str:
    """Render one or more differential reports into the shared row layout."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "entity_id",
            "condition_a",
            "condition_b",
            "contrast_name",
            "observations_a",
            "observations_b",
            "complete_pair_count",
            "zero_values_a",
            "zero_values_b",
            "not_observed_values_a",
            "not_observed_values_b",
            "filtered_values_a",
            "filtered_values_b",
            "mean_log2_abundance_a",
            "mean_log2_abundance_b",
            "log2_fold_change",
            "p_value",
            "adjusted_p_value",
            "standard_error",
            "confidence_interval_low",
            "confidence_interval_high",
            "effect_size_cohens_d",
            "no_impute_adjusted_p_value",
            "no_impute_log2_fold_change",
            "imputed_adjusted_p_value",
            "imputed_log2_fold_change",
            "imputation_significance_change_reason",
            "imputation_dependent_hit",
            "robustness_score",
            "robustness_qc_status",
            "robustness_reason_codes",
            "robustness_note",
            "uncertainty_note",
        ]
    )
    for report in reports:
        for entry in report.entries:
            writer.writerow(
                [
                    entry.entity_id,
                    entry.condition_a,
                    entry.condition_b,
                    report.contrast_name or "",
                    entry.observations_a,
                    entry.observations_b,
                    entry.complete_pair_count,
                    entry.zero_values_a,
                    entry.zero_values_b,
                    entry.not_observed_values_a,
                    entry.not_observed_values_b,
                    entry.filtered_values_a,
                    entry.filtered_values_b,
                    entry.mean_log2_abundance_a,
                    entry.mean_log2_abundance_b,
                    entry.log2_fold_change,
                    entry.p_value,
                    "" if entry.adjusted_p_value is None else entry.adjusted_p_value,
                    "" if entry.standard_error is None else entry.standard_error,
                    (
                        ""
                        if entry.confidence_interval_low is None
                        else entry.confidence_interval_low
                    ),
                    (
                        ""
                        if entry.confidence_interval_high is None
                        else entry.confidence_interval_high
                    ),
                    (
                        ""
                        if entry.effect_size_cohens_d is None
                        else entry.effect_size_cohens_d
                    ),
                    (
                        ""
                        if entry.no_impute_adjusted_p_value is None
                        else entry.no_impute_adjusted_p_value
                    ),
                    (
                        ""
                        if entry.no_impute_log2_fold_change is None
                        else entry.no_impute_log2_fold_change
                    ),
                    (
                        ""
                        if entry.imputed_adjusted_p_value is None
                        else entry.imputed_adjusted_p_value
                    ),
                    (
                        ""
                        if entry.imputed_log2_fold_change is None
                        else entry.imputed_log2_fold_change
                    ),
                    (
                        ""
                        if entry.imputation_significance_change_reason is None
                        else entry.imputation_significance_change_reason.value
                    ),
                    str(entry.imputation_dependent_hit).lower(),
                    ("" if entry.robustness_score is None else entry.robustness_score),
                    (
                        ""
                        if entry.robustness_qc_status is None
                        else entry.robustness_qc_status.value
                    ),
                    ";".join(reason.value for reason in entry.robustness_reason_codes),
                    entry.robustness_note or "",
                    entry.uncertainty_note or "",
                ]
            )
    return buffer.getvalue()


__all__ = [
    "export_differential_abundance_tsv",
    "export_differential_broken_pairs_tsv",
    "export_multi_condition_differential_abundance_tsv",
    "render_differential_abundance_tsv",
    "render_differential_broken_pairs_tsv",
    "render_multi_condition_differential_abundance_tsv",
]
