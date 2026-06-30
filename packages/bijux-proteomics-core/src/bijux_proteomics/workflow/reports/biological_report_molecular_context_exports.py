# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Molecular-context artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class BiologicalDrugTargetExportNames:
    """Artifact names emitted for drug-target interpretation exports."""

    summary_name: str | None
    interpretation_name: str | None


@dataclass(frozen=True)
class BiologicalDiseasePhenotypeExportNames:
    """Artifact names emitted for disease-phenotype interpretation exports."""

    summary_name: str | None
    term_name: str | None
    unknown_name: str | None


def _write_biological_drug_target_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalDrugTargetExportNames:
    if report.drug_target_report is None:
        return BiologicalDrugTargetExportNames(
            summary_name=None,
            interpretation_name=None,
        )

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
    return BiologicalDrugTargetExportNames(
        summary_name=summary_name,
        interpretation_name=interpretation_name,
    )


def _write_biological_disease_phenotype_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalDiseasePhenotypeExportNames:
    if report.disease_phenotype_report is None:
        return BiologicalDiseasePhenotypeExportNames(
            summary_name=None,
            term_name=None,
            unknown_name=None,
        )

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
    return BiologicalDiseasePhenotypeExportNames(
        summary_name=summary_name,
        term_name=term_name,
        unknown_name=unknown_name,
    )


__all__ = [
    "BiologicalDiseasePhenotypeExportNames",
    "BiologicalDrugTargetExportNames",
    "_write_biological_disease_phenotype_exports",
    "_write_biological_drug_target_exports",
]
