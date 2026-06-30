# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sample-context artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)


def _write_biological_cohort_context_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None]:
    if report.cohort_stratification_report is None:
        return (None, None, None, None)

    summary_name = "biological_cohort_stratification_summary.tsv"
    stratum_name = "biological_cohort_strata.tsv"
    effect_name = "biological_cohort_subgroup_effects.tsv"
    interaction_name = "biological_cohort_interaction_candidates.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_cohort_stratification_summary_tsv(report.cohort_stratification_report),
    )
    write_output_table_tsv(
        output_dir / stratum_name,
        render_cohort_stratum_tsv(report.cohort_stratification_report),
    )
    write_output_table_tsv(
        output_dir / effect_name,
        render_cohort_subgroup_effect_tsv(report.cohort_stratification_report),
    )
    write_output_table_tsv(
        output_dir / interaction_name,
        render_cohort_interaction_candidate_tsv(report.cohort_stratification_report),
    )
    return (
        summary_name,
        stratum_name,
        effect_name,
        interaction_name,
    )


def _write_biological_tissue_context_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None]:
    if report.tissue_cell_type_context_report is None:
        return (None, None, None, None)

    summary_name = "biological_tissue_context_summary.tsv"
    sample_name = "biological_tissue_context_sample_consistency.tsv"
    unexpected_name = "biological_tissue_context_unexpected_signals.tsv"
    interpretation_name = "biological_tissue_context_interpretation.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_tissue_cell_type_context_summary_tsv(
            report.tissue_cell_type_context_report
        ),
    )
    write_output_table_tsv(
        output_dir / sample_name,
        render_tissue_cell_type_sample_consistency_tsv(
            report.tissue_cell_type_context_report
        ),
    )
    write_output_table_tsv(
        output_dir / unexpected_name,
        render_tissue_cell_type_unexpected_signal_tsv(
            report.tissue_cell_type_context_report
        ),
    )
    write_output_table_tsv(
        output_dir / interpretation_name,
        render_tissue_cell_type_interpretation_tsv(
            report.tissue_cell_type_context_report
        ),
    )
    return (
        summary_name,
        sample_name,
        unexpected_name,
        interpretation_name,
    )
