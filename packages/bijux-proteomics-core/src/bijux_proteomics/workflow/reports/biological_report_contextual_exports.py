# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contextual artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_annotation_context_exports import (
    _write_biological_annotation_context_exports,
)
from bijux_proteomics.workflow.reports.biological_report_molecular_context_exports import (
    _write_biological_disease_phenotype_exports,
    _write_biological_drug_target_exports,
)
from bijux_proteomics.workflow.reports.biological_report_sample_context_exports import (
    _write_biological_cohort_context_exports,
    _write_biological_tissue_context_exports,
)


@dataclass(frozen=True)
class BiologicalContextualExportNames:
    """Artifact names emitted for contextual biological report sections."""

    context_summary_name: str | None
    context_mapping_name: str | None
    context_term_name: str | None
    context_unmapped_name: str | None
    context_rejected_name: str | None
    cohort_summary_name: str | None
    cohort_stratum_name: str | None
    cohort_effect_name: str | None
    cohort_interaction_name: str | None
    tissue_context_summary_name: str | None
    tissue_context_sample_name: str | None
    tissue_context_unexpected_name: str | None
    tissue_context_interpretation_name: str | None
    drug_target_summary_name: str | None
    drug_target_name: str | None
    disease_phenotype_summary_name: str | None
    disease_phenotype_term_name: str | None
    disease_phenotype_unknown_name: str | None


def write_biological_contextual_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalContextualExportNames:
    """Write optional contextual report artifacts."""

    annotation_export_names = _write_biological_annotation_context_exports(
        report, output_dir
    )
    cohort_export_names = _write_biological_cohort_context_exports(report, output_dir)
    tissue_export_names = _write_biological_tissue_context_exports(report, output_dir)
    drug_target_export_names = _write_biological_drug_target_exports(
        report, output_dir
    )
    disease_phenotype_export_names = _write_biological_disease_phenotype_exports(
        report, output_dir
    )

    return BiologicalContextualExportNames(
        context_summary_name=annotation_export_names.summary_name,
        context_mapping_name=annotation_export_names.mapping_name,
        context_term_name=annotation_export_names.term_name,
        context_unmapped_name=annotation_export_names.unmapped_name,
        context_rejected_name=annotation_export_names.rejected_name,
        cohort_summary_name=cohort_export_names.summary_name,
        cohort_stratum_name=cohort_export_names.stratum_name,
        cohort_effect_name=cohort_export_names.effect_name,
        cohort_interaction_name=cohort_export_names.interaction_name,
        tissue_context_summary_name=tissue_export_names.summary_name,
        tissue_context_sample_name=tissue_export_names.sample_name,
        tissue_context_unexpected_name=tissue_export_names.unexpected_name,
        tissue_context_interpretation_name=tissue_export_names.interpretation_name,
        drug_target_summary_name=drug_target_export_names.summary_name,
        drug_target_name=drug_target_export_names.interpretation_name,
        disease_phenotype_summary_name=disease_phenotype_export_names.summary_name,
        disease_phenotype_term_name=disease_phenotype_export_names.term_name,
        disease_phenotype_unknown_name=disease_phenotype_export_names.unknown_name,
    )
