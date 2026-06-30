# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Activity artifact-path assembly for biological report manifests."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_activity_exports import (
    BiologicalActivityExportNames,
)


def _build_biological_activity_artifact_path_fields(
    activity_export_names: BiologicalActivityExportNames,
) -> dict[str, str | None]:
    return {
        "pathway_card_tsv": activity_export_names.pathway_card_name,
        "compartment_biology_summary_tsv": activity_export_names.compartment_summary_name,
        "compartment_enrichment_tsv": activity_export_names.compartment_enrichment_name,
        "compartment_activity_matrix_tsv": activity_export_names.compartment_activity_matrix_name,
        "compartment_activity_sample_score_tsv": activity_export_names.compartment_activity_sample_name,
        "compartment_activity_condition_score_tsv": activity_export_names.compartment_activity_condition_name,
        "compartment_activity_condition_comparison_tsv": activity_export_names.compartment_activity_comparison_name,
        "compartment_activity_unresolved_member_tsv": activity_export_names.compartment_activity_unresolved_name,
        "compartment_unknown_localization_tsv": activity_export_names.compartment_unknown_name,
        "pathway_activity_summary_tsv": activity_export_names.pathway_activity_summary_name,
        "pathway_activity_matrix_tsv": activity_export_names.pathway_activity_matrix_name,
        "pathway_activity_sample_score_tsv": activity_export_names.pathway_activity_sample_name,
        "pathway_activity_condition_score_tsv": activity_export_names.pathway_activity_condition_name,
        "pathway_activity_condition_comparison_tsv": activity_export_names.pathway_activity_comparison_name,
        "pathway_activity_member_contribution_tsv": activity_export_names.pathway_activity_member_name,
        "pathway_activity_unresolved_member_tsv": activity_export_names.pathway_activity_unresolved_name,
        "complex_activity_summary_tsv": activity_export_names.complex_activity_summary_name,
        "complex_activity_matrix_tsv": activity_export_names.complex_activity_matrix_name,
        "complex_activity_sample_score_tsv": activity_export_names.complex_activity_sample_name,
        "complex_activity_condition_score_tsv": activity_export_names.complex_activity_condition_name,
        "complex_activity_condition_comparison_tsv": activity_export_names.complex_activity_comparison_name,
        "complex_activity_member_contribution_tsv": activity_export_names.complex_activity_member_name,
        "complex_activity_unresolved_member_tsv": activity_export_names.complex_activity_unresolved_name,
    }
