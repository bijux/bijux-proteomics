# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contextual artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_rejected_biological_context_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    render_unmapped_biological_context_tsv,
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

    context_summary_name = None
    context_mapping_name = None
    context_term_name = None
    context_unmapped_name = None
    context_rejected_name = None
    if (
        report.context_import_report is not None
        and report.context_mapping_report is not None
    ):
        context_summary_name = "biological_context_summary.tsv"
        context_mapping_name = "biological_context_mappings.tsv"
        context_term_name = "biological_context_terms.tsv"
        context_unmapped_name = "biological_context_unmapped.tsv"
        context_rejected_name = "biological_context_rejected.tsv"
        write_output_table_tsv(
            output_dir / context_summary_name,
            render_biological_context_mapping_summary_tsv(
                report.context_mapping_report
            ),
        )
        write_output_table_tsv(
            output_dir / context_mapping_name,
            render_biological_context_mapping_tsv(report.context_mapping_report),
        )
        write_output_table_tsv(
            output_dir / context_term_name,
            render_biological_context_term_tsv(report.context_mapping_report),
        )
        write_output_table_tsv(
            output_dir / context_unmapped_name,
            render_unmapped_biological_context_tsv(report.context_mapping_report),
        )
        write_output_table_tsv(
            output_dir / context_rejected_name,
            render_rejected_biological_context_tsv(report.context_import_report),
        )

    cohort_summary_name = None
    cohort_stratum_name = None
    cohort_effect_name = None
    cohort_interaction_name = None
    if report.cohort_stratification_report is not None:
        cohort_summary_name = "biological_cohort_stratification_summary.tsv"
        cohort_stratum_name = "biological_cohort_strata.tsv"
        cohort_effect_name = "biological_cohort_subgroup_effects.tsv"
        cohort_interaction_name = "biological_cohort_interaction_candidates.tsv"
        write_output_table_tsv(
            output_dir / cohort_summary_name,
            render_cohort_stratification_summary_tsv(
                report.cohort_stratification_report
            ),
        )
        write_output_table_tsv(
            output_dir / cohort_stratum_name,
            render_cohort_stratum_tsv(report.cohort_stratification_report),
        )
        write_output_table_tsv(
            output_dir / cohort_effect_name,
            render_cohort_subgroup_effect_tsv(report.cohort_stratification_report),
        )
        write_output_table_tsv(
            output_dir / cohort_interaction_name,
            render_cohort_interaction_candidate_tsv(
                report.cohort_stratification_report
            ),
        )

    tissue_context_summary_name = None
    tissue_context_sample_name = None
    tissue_context_unexpected_name = None
    tissue_context_interpretation_name = None
    if report.tissue_cell_type_context_report is not None:
        tissue_context_summary_name = "biological_tissue_context_summary.tsv"
        tissue_context_sample_name = "biological_tissue_context_sample_consistency.tsv"
        tissue_context_unexpected_name = (
            "biological_tissue_context_unexpected_signals.tsv"
        )
        tissue_context_interpretation_name = (
            "biological_tissue_context_interpretation.tsv"
        )
        write_output_table_tsv(
            output_dir / tissue_context_summary_name,
            render_tissue_cell_type_context_summary_tsv(
                report.tissue_cell_type_context_report
            ),
        )
        write_output_table_tsv(
            output_dir / tissue_context_sample_name,
            render_tissue_cell_type_sample_consistency_tsv(
                report.tissue_cell_type_context_report
            ),
        )
        write_output_table_tsv(
            output_dir / tissue_context_unexpected_name,
            render_tissue_cell_type_unexpected_signal_tsv(
                report.tissue_cell_type_context_report
            ),
        )
        write_output_table_tsv(
            output_dir / tissue_context_interpretation_name,
            render_tissue_cell_type_interpretation_tsv(
                report.tissue_cell_type_context_report
            ),
        )

    drug_target_summary_name = None
    drug_target_name = None
    if report.drug_target_report is not None:
        drug_target_summary_name = "biological_drug_target_summary.tsv"
        drug_target_name = "biological_drug_target_interpretation.tsv"
        write_output_table_tsv(
            output_dir / drug_target_summary_name,
            render_drug_target_interpretation_summary_tsv(report.drug_target_report),
        )
        write_output_table_tsv(
            output_dir / drug_target_name,
            render_drug_target_interpretation_tsv(report.drug_target_report),
        )

    disease_phenotype_summary_name = None
    disease_phenotype_term_name = None
    disease_phenotype_unknown_name = None
    if report.disease_phenotype_report is not None:
        disease_phenotype_summary_name = "biological_disease_phenotype_summary.tsv"
        disease_phenotype_term_name = "biological_disease_phenotype_terms.tsv"
        disease_phenotype_unknown_name = (
            "biological_disease_phenotype_unknown_annotations.tsv"
        )
        write_output_table_tsv(
            output_dir / disease_phenotype_summary_name,
            render_disease_phenotype_interpretation_summary_tsv(
                report.disease_phenotype_report
            ),
        )
        write_output_table_tsv(
            output_dir / disease_phenotype_term_name,
            render_disease_phenotype_interpretation_tsv(
                report.disease_phenotype_report
            ),
        )
        write_output_table_tsv(
            output_dir / disease_phenotype_unknown_name,
            render_unknown_disease_phenotype_annotation_tsv(
                report.disease_phenotype_report
            ),
        )

    return BiologicalContextualExportNames(
        context_summary_name=context_summary_name,
        context_mapping_name=context_mapping_name,
        context_term_name=context_term_name,
        context_unmapped_name=context_unmapped_name,
        context_rejected_name=context_rejected_name,
        cohort_summary_name=cohort_summary_name,
        cohort_stratum_name=cohort_stratum_name,
        cohort_effect_name=cohort_effect_name,
        cohort_interaction_name=cohort_interaction_name,
        tissue_context_summary_name=tissue_context_summary_name,
        tissue_context_sample_name=tissue_context_sample_name,
        tissue_context_unexpected_name=tissue_context_unexpected_name,
        tissue_context_interpretation_name=tissue_context_interpretation_name,
        drug_target_summary_name=drug_target_summary_name,
        drug_target_name=drug_target_name,
        disease_phenotype_summary_name=disease_phenotype_summary_name,
        disease_phenotype_term_name=disease_phenotype_term_name,
        disease_phenotype_unknown_name=disease_phenotype_unknown_name,
    )
