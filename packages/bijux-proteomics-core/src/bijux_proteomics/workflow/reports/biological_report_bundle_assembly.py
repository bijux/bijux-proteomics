# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned final bundle composition for biological report assembly."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_bundle_assembly_inputs import (
    BiologicalReportBundleAssemblyInputs,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_confidence_state import (
    _build_biological_report_bundle_confidence_state,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_materialization import (
    _materialize_biological_result_report_bundle,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_summary import (
    _build_biological_result_report_summary,
)


def _assemble_biological_result_report_bundle(
    assembly_inputs: BiologicalReportBundleAssemblyInputs,
) -> BiologicalResultReportBundle:
    confidence_state = _build_biological_report_bundle_confidence_state(
        experiment_confidence_report=assembly_inputs.experiment_confidence_report,
        evidence_aware_ranking_report=assembly_inputs.evidence_aware_ranking_report,
        claim_validation_report=assembly_inputs.claim_validation_report,
        biological_hypothesis_report=assembly_inputs.biological_hypothesis_report,
        foreground_background_model=assembly_inputs.foreground_background_model,
        regulator_inference_report=assembly_inputs.regulator_inference_report,
        drug_target_report=assembly_inputs.drug_target_report,
        disease_phenotype_report=assembly_inputs.disease_phenotype_report,
        cohort_stratification_report=assembly_inputs.cohort_stratification_report,
        tissue_cell_type_context_report=(
            assembly_inputs.tissue_cell_type_context_report
        ),
        compartment_biology_report=assembly_inputs.compartment_biology_report,
        pathway_activity_report=assembly_inputs.pathway_activity_report,
        complex_activity_report=assembly_inputs.complex_activity_report,
        protein_mechanism_cards=assembly_inputs.protein_mechanism_cards,
    )
    return _materialize_biological_result_report_bundle(
        differential_report=assembly_inputs.differential_report,
        graph_report=assembly_inputs.graph_report,
        annotation_report=assembly_inputs.annotation_report,
        protein_cards=assembly_inputs.protein_cards,
        protein_mechanism_cards=assembly_inputs.protein_mechanism_cards,
        experiment_confidence_report=assembly_inputs.experiment_confidence_report,
        evidence_aware_ranking_report=assembly_inputs.evidence_aware_ranking_report,
        claim_validation_report=assembly_inputs.claim_validation_report,
        biological_hypothesis_report=assembly_inputs.biological_hypothesis_report,
        foreground_background_model=assembly_inputs.foreground_background_model,
        regulator_evidence_import_report=(
            assembly_inputs.regulator_evidence_import_report
        ),
        regulator_inference_report=assembly_inputs.regulator_inference_report,
        context_import_report=assembly_inputs.context_import_report,
        context_mapping_report=assembly_inputs.context_mapping_report,
        cohort_stratification_report=assembly_inputs.cohort_stratification_report,
        tissue_cell_type_context_report=assembly_inputs.tissue_cell_type_context_report,
        drug_target_report=assembly_inputs.drug_target_report,
        disease_phenotype_report=assembly_inputs.disease_phenotype_report,
        compartment_biology_report=assembly_inputs.compartment_biology_report,
        pathway_activity_report=assembly_inputs.pathway_activity_report,
        complex_activity_report=assembly_inputs.complex_activity_report,
        go_enrichment_report=assembly_inputs.go_enrichment_report,
        pathway_enrichment_report=assembly_inputs.pathway_enrichment_report,
        complex_enrichment_report=assembly_inputs.complex_enrichment_report,
        volcano_review=assembly_inputs.volcano_review,
        heatmap_report=assembly_inputs.heatmap_report,
        sample_exploration_report=assembly_inputs.sample_exploration_report,
        selection_policy=assembly_inputs.selection_policy,
        section_confidence_entries=confidence_state.entries,
        summary=_build_biological_result_report_summary(
            normalized_table=assembly_inputs.normalized_table,
            differential_report=assembly_inputs.differential_report,
            selection_policy=assembly_inputs.selection_policy,
            annotation_report=assembly_inputs.annotation_report,
            protein_cards=assembly_inputs.protein_cards,
            tissue_cell_type_context_report=(
                assembly_inputs.tissue_cell_type_context_report
            ),
            cohort_stratification_report=assembly_inputs.cohort_stratification_report,
            experiment_confidence_report=assembly_inputs.experiment_confidence_report,
            section_confidence_counts=confidence_state.counts,
            context_mapping_report=assembly_inputs.context_mapping_report,
            go_enrichment_report=assembly_inputs.go_enrichment_report,
            pathway_enrichment_report=assembly_inputs.pathway_enrichment_report,
            complex_enrichment_report=assembly_inputs.complex_enrichment_report,
            heatmap_report=assembly_inputs.heatmap_report,
            sample_exploration_report=assembly_inputs.sample_exploration_report,
        ),
    )
