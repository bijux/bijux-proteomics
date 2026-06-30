# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Final scientific export-name assembly for biological reports."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_claim_exports import (
    BiologicalClaimExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_exports import (
    BiologicalHypothesisExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_exports import (
    BiologicalRankingExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_exports import (
    BiologicalRegulatorExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_export_contracts import (
    BiologicalScientificExportNames,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_required_exports import (
    BiologicalScientificRequiredExportNames,
)


def _build_biological_scientific_export_names(
    *,
    required_export_names: BiologicalScientificRequiredExportNames,
    ranking_export_names: BiologicalRankingExportNames,
    claim_export_names: BiologicalClaimExportNames,
    hypothesis_export_names: BiologicalHypothesisExportNames,
    regulator_export_names: BiologicalRegulatorExportNames,
) -> BiologicalScientificExportNames:
    return BiologicalScientificExportNames(
        summary_name=required_export_names.summary_name,
        differential_name=required_export_names.differential_name,
        protein_card_summary_name=required_export_names.protein_card_summary_name,
        protein_card_name=required_export_names.protein_card_name,
        protein_mechanism_card_summary_name=(
            required_export_names.protein_mechanism_card_summary_name
        ),
        protein_mechanism_card_name=required_export_names.protein_mechanism_card_name,
        evidence_graph_nodes_name=required_export_names.evidence_graph_nodes_name,
        evidence_graph_edges_name=required_export_names.evidence_graph_edges_name,
        experiment_confidence_summary_name=(
            required_export_names.experiment_confidence_summary_name
        ),
        experiment_confidence_components_name=(
            required_export_names.experiment_confidence_components_name
        ),
        section_confidence_name=required_export_names.section_confidence_name,
        evidence_aware_ranking_name=ranking_export_names.evidence_aware_ranking_name,
        claim_validation_summary_name=(
            claim_export_names.claim_validation_summary_name
        ),
        supported_claim_name=claim_export_names.supported_claim_name,
        rejected_claim_name=claim_export_names.rejected_claim_name,
        biological_hypothesis_summary_name=(
            hypothesis_export_names.biological_hypothesis_summary_name
        ),
        biological_hypothesis_name=hypothesis_export_names.biological_hypothesis_name,
        rejected_hypothesis_candidate_name=(
            hypothesis_export_names.rejected_hypothesis_candidate_name
        ),
        foreground_background_summary_name=(
            required_export_names.foreground_background_summary_name
        ),
        foreground_background_entry_name=(
            required_export_names.foreground_background_entry_name
        ),
        foreground_background_issue_name=(
            required_export_names.foreground_background_issue_name
        ),
        regulator_inference_summary_name=(
            regulator_export_names.regulator_inference_summary_name
        ),
        regulator_inference_name=regulator_export_names.regulator_inference_name,
        regulator_unresolved_name=regulator_export_names.regulator_unresolved_name,
        regulator_rejected_name=regulator_export_names.regulator_rejected_name,
        annotation_summary_name=required_export_names.annotation_summary_name,
        annotation_name=required_export_names.annotation_name,
        annotation_unmapped_name=required_export_names.annotation_unmapped_name,
    )


__all__ = ["_build_biological_scientific_export_names"]
