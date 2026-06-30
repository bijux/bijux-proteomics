# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway activity artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_member_contribution_tsv,
)
from bijux_proteomics.workflow.cards.pathway_evidence_cards import (
    render_pathway_evidence_card_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _write_biological_pathway_activity_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None, str | None, str | None]:
    if report.pathway_activity_report is None:
        return (None, None, None, None, None, None, None, None)

    card_name = "biological_pathway_cards.tsv"
    activity_summary_name = "biological_pathway_activity_summary.tsv"
    activity_matrix_name = "biological_pathway_activity_matrix.tsv"
    activity_sample_name = "biological_pathway_activity_samples.tsv"
    activity_condition_name = "biological_pathway_activity_conditions.tsv"
    activity_comparison_name = (
        "biological_pathway_activity_condition_comparisons.tsv"
    )
    activity_member_name = "biological_pathway_activity_members.tsv"
    activity_unresolved_name = "biological_pathway_activity_unresolved.tsv"
    write_output_table_tsv(
        output_dir / activity_summary_name,
        render_pathway_activity_summary_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / card_name,
        render_pathway_evidence_card_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_matrix_name,
        render_pathway_activity_matrix_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_sample_name,
        render_pathway_activity_sample_score_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_condition_name,
        render_pathway_activity_condition_score_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_comparison_name,
        render_pathway_activity_condition_comparison_tsv(
            report.pathway_activity_report
        ),
    )
    write_output_table_tsv(
        output_dir / activity_member_name,
        render_pathway_member_contribution_tsv(report.pathway_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_unresolved_name,
        render_pathway_activity_unresolved_member_tsv(report.pathway_activity_report),
    )
    return (
        card_name,
        activity_summary_name,
        activity_matrix_name,
        activity_sample_name,
        activity_condition_name,
        activity_comparison_name,
        activity_member_name,
        activity_unresolved_name,
    )
