# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Molecular-context artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _write_biological_drug_target_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None]:
    if report.drug_target_report is None:
        return (None, None)

    summary_name = "biological_drug_target_summary.tsv"
    interpretation_name = "biological_drug_target_interpretation.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_drug_target_interpretation_summary_tsv(report.drug_target_report),
    )
    write_output_table_tsv(
        output_dir / interpretation_name,
        render_drug_target_interpretation_tsv(report.drug_target_report),
    )
    return (summary_name, interpretation_name)


def _write_biological_disease_phenotype_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None]:
    if report.disease_phenotype_report is None:
        return (None, None, None)

    summary_name = "biological_disease_phenotype_summary.tsv"
    term_name = "biological_disease_phenotype_terms.tsv"
    unknown_name = "biological_disease_phenotype_unknown_annotations.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_disease_phenotype_interpretation_summary_tsv(
            report.disease_phenotype_report
        ),
    )
    write_output_table_tsv(
        output_dir / term_name,
        render_disease_phenotype_interpretation_tsv(
            report.disease_phenotype_report
        ),
    )
    write_output_table_tsv(
        output_dir / unknown_name,
        render_unknown_disease_phenotype_annotation_tsv(
            report.disease_phenotype_report
        ),
    )
    return (summary_name, term_name, unknown_name)
