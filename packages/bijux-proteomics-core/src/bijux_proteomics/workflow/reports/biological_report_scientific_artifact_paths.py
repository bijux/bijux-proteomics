# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific artifact-path assembly for biological report manifests."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_scientific_exports import (
    BiologicalScientificExportNames,
)


def _build_biological_scientific_artifact_path_fields(
    scientific_export_names: BiologicalScientificExportNames,
) -> dict[str, str | None]:
    return {
        "summary_tsv": scientific_export_names.summary_name,
        "differential_tsv": scientific_export_names.differential_name,
        "protein_card_summary_tsv": scientific_export_names.protein_card_summary_name,
        "protein_card_tsv": scientific_export_names.protein_card_name,
        "protein_mechanism_card_summary_tsv": (
            scientific_export_names.protein_mechanism_card_summary_name
        ),
        "protein_mechanism_card_tsv": scientific_export_names.protein_mechanism_card_name,
        "evidence_graph_nodes_tsv": scientific_export_names.evidence_graph_nodes_name,
        "evidence_graph_edges_tsv": scientific_export_names.evidence_graph_edges_name,
        "experiment_confidence_summary_tsv": (
            scientific_export_names.experiment_confidence_summary_name
        ),
        "experiment_confidence_components_tsv": (
            scientific_export_names.experiment_confidence_components_name
        ),
        "section_confidence_tsv": scientific_export_names.section_confidence_name,
        "evidence_aware_ranking_tsv": scientific_export_names.evidence_aware_ranking_name,
        "claim_validation_summary_tsv": (
            scientific_export_names.claim_validation_summary_name
        ),
        "supported_claim_tsv": scientific_export_names.supported_claim_name,
        "rejected_claim_tsv": scientific_export_names.rejected_claim_name,
        "biological_hypothesis_summary_tsv": (
            scientific_export_names.biological_hypothesis_summary_name
        ),
        "biological_hypothesis_tsv": scientific_export_names.biological_hypothesis_name,
        "rejected_hypothesis_candidate_tsv": (
            scientific_export_names.rejected_hypothesis_candidate_name
        ),
        "foreground_background_summary_tsv": (
            scientific_export_names.foreground_background_summary_name
        ),
        "foreground_background_entry_tsv": (
            scientific_export_names.foreground_background_entry_name
        ),
        "foreground_background_issue_tsv": (
            scientific_export_names.foreground_background_issue_name
        ),
        "regulator_inference_summary_tsv": (
            scientific_export_names.regulator_inference_summary_name
        ),
        "regulator_inference_tsv": scientific_export_names.regulator_inference_name,
        "regulator_inference_unresolved_tsv": (
            scientific_export_names.regulator_unresolved_name
        ),
        "regulator_evidence_rejected_tsv": scientific_export_names.regulator_rejected_name,
        "annotation_summary_tsv": scientific_export_names.annotation_summary_name,
        "annotation_tsv": scientific_export_names.annotation_name,
        "annotation_unmapped_tsv": scientific_export_names.annotation_unmapped_name,
    }
