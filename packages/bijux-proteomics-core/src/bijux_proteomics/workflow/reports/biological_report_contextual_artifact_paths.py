# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contextual artifact-path assembly for biological report manifests."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_contextual_exports import (
    BiologicalContextualExportNames,
)


def _build_biological_contextual_artifact_path_fields(
    contextual_export_names: BiologicalContextualExportNames,
) -> dict[str, str | None]:
    return {
        "context_summary_tsv": contextual_export_names.context_summary_name,
        "context_mapping_tsv": contextual_export_names.context_mapping_name,
        "context_term_tsv": contextual_export_names.context_term_name,
        "context_unmapped_tsv": contextual_export_names.context_unmapped_name,
        "context_rejected_tsv": contextual_export_names.context_rejected_name,
        "cohort_stratification_summary_tsv": contextual_export_names.cohort_summary_name,
        "cohort_stratum_tsv": contextual_export_names.cohort_stratum_name,
        "cohort_subgroup_effect_tsv": contextual_export_names.cohort_effect_name,
        "cohort_interaction_candidate_tsv": contextual_export_names.cohort_interaction_name,
        "tissue_context_summary_tsv": contextual_export_names.tissue_context_summary_name,
        "tissue_context_sample_consistency_tsv": contextual_export_names.tissue_context_sample_name,
        "tissue_context_unexpected_signal_tsv": contextual_export_names.tissue_context_unexpected_name,
        "tissue_context_interpretation_tsv": contextual_export_names.tissue_context_interpretation_name,
        "drug_target_summary_tsv": contextual_export_names.drug_target_summary_name,
        "drug_target_tsv": contextual_export_names.drug_target_name,
        "disease_phenotype_summary_tsv": contextual_export_names.disease_phenotype_summary_name,
        "disease_phenotype_term_tsv": contextual_export_names.disease_phenotype_term_name,
        "disease_phenotype_unknown_annotation_tsv": contextual_export_names.disease_phenotype_unknown_name,
    }
