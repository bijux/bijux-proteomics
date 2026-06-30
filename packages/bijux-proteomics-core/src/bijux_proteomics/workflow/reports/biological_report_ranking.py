# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Biological ranking construction helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation import (
    BiologicalContextImportReport,
    BiologicalContextKind,
    BiologicalContextMappingReport,
    BiologicalForegroundBackgroundModel,
    BiologicalSetEntry,
    BiologicalSetFilteringPolicy,
    BiologicalSetSourceKind,
    ComplexActivityReport,
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
    DiseasePhenotypeInterpretationPolicy,
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationPolicy,
    DrugTargetInterpretationReport,
    GoEnrichmentCorrectionPolicy,
    GoEnrichmentReport,
    PathwayActivityReport,
    PathwayEnrichmentCorrectionPolicy,
    PathwayEnrichmentReport,
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinReferenceEntry,
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    TissueCellTypeContextReport,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_biological_context_mapping_report,
    build_biological_foreground_background_model,
    build_complex_activity_report,
    build_complex_enrichment_report,
    build_disease_phenotype_interpretation_report,
    build_drug_target_interpretation_report,
    build_go_enrichment_report,
    build_pathway_activity_report,
    build_pathway_enrichment_report,
    build_protein_annotation_mapping_report,
    build_regulator_inference_report,
    build_regulator_site_signal_entries_from_ptm_evidence_cards,
    build_tissue_cell_type_context_report,
    parse_biological_context_table,
    parse_complex_membership_table,
    parse_go_annotation_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    parse_regulator_evidence_table,
    parse_regulator_site_signal_table,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_biological_foreground_background_entry_tsv,
    render_biological_foreground_background_issue_tsv,
    render_biological_foreground_background_summary_tsv,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_member_contribution_tsv,
    render_complex_unresolved_member_tsv,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_member_contribution_tsv,
    render_pathway_unresolved_member_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_rejected_biological_context_tsv,
    render_rejected_regulator_evidence_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    render_unmapped_biological_context_tsv,
    render_unmapped_protein_annotation_tsv,
    render_unresolved_regulator_target_tsv,
    require_valid_biological_foreground_background_model,
)
from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyPolicy,
    CompartmentBiologyReport,
    build_compartment_biology_report,
    render_compartment_activity_condition_comparison_tsv,
    render_compartment_activity_condition_score_tsv,
    render_compartment_activity_matrix_tsv,
    render_compartment_activity_sample_score_tsv,
    render_compartment_activity_unresolved_member_tsv,
    render_compartment_biology_summary_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
)
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
)
from bijux_proteomics.quantification.normalization import (
    normalize_label_free_table,
)
from bijux_proteomics.quantification.provenance import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    SampleExplorationReport,
    build_heatmap_preparation_report,
    build_sample_exploration_report,
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
)
from bijux_proteomics.quantification.statistics import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_power_estimation_report,
    render_differential_abundance_tsv,
)
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    EvidenceAwareRankingReport,
    build_evidence_aware_ranking_report,
    normalize_linear_range,
    render_evidence_aware_ranking_tsv,
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    build_biological_claim_validation_report,
    render_biological_claim_validation_summary_tsv,
    render_rejected_biological_claim_tsv,
    render_supported_biological_claim_tsv,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
    BiologicalHypothesisReport,
    build_biological_hypothesis_report,
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_export import (
    export_proteomics_evidence_graph,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_quantification_volcano_review,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_volcano_review_tsv,
)
from bijux_proteomics.sequences.fasta import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.protein_region_context_workflows import (
    parse_protein_region_context_tsv,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    parse_proteogenomic_variant_peptide_table,
)
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
    coerce_experiment_design,
    render_experiment_confidence_component_tsv,
    render_experiment_confidence_summary_tsv,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCard,
    ProteinEvidenceCardReport,
    ProteinEvidenceCardSelectionPolicy,
    build_protein_evidence_card_report,
    render_protein_evidence_card_summary_tsv,
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
    build_protein_mechanism_card_report,
    render_protein_mechanism_card_summary_tsv,
    render_protein_mechanism_card_tsv,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)
from bijux_proteomics_foundation import JsonModel


def _build_biological_protein_ranking_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    mechanism_by_protein_group = {
        card.protein_group_id: card for card in protein_mechanism_cards.cards
    }
    abundance_by_entity = {
        card.protein_group_id: max(
            card.differential_result.mean_log2_abundance_a,
            card.differential_result.mean_log2_abundance_b,
        )
        for card in protein_cards.cards
    }
    abundance_scores = normalize_linear_range(abundance_by_entity)

    candidates: list[EvidenceAwareRankingCandidate] = []
    for protein_card in protein_cards.cards:
        mechanism_card = mechanism_by_protein_group.get(protein_card.protein_group_id)
        if mechanism_card is None:
            raise ValueError(
                "biological evidence-aware ranking requires one protein mechanism card per protein card"
            )
        differential_entry = differential_by_entity.get(protein_card.protein_group_id)
        if differential_entry is None:
            raise ValueError(
                "biological evidence-aware ranking requires one differential entry per protein card"
            )
        abundance_value = abundance_by_entity[protein_card.protein_group_id]
        unique_support = mechanism_card.peptide_support.unique_peptide_count
        support_score = min(
            1.0,
            (0.7 * score_support_count(unique_support, saturation=4))
            + (
                0.3
                * score_support_count(
                    mechanism_card.peptide_support.quantifying_peptide_count,
                    saturation=6,
                )
            ),
        )
        annotation_score = min(
            1.0,
            (
                0.45
                if protein_card.annotation.annotation_status.value != "unmapped"
                else 0.0
            )
            + (0.15 if protein_card.functional_regions else 0.0)
            + (0.15 if protein_card.pathways else 0.0)
            + (0.15 if protein_card.ptm_sites else 0.0)
            + (0.10 if protein_card.context_terms else 0.0),
        )
        confidence_score = min(
            1.0,
            (
                0.45 * _tier_score(mechanism_card.confidence_tier.value)
                + 0.35 * _tier_score(mechanism_card.evidence_tier.value)
                + max(0.0, 0.2 - (0.04 * len(mechanism_card.downgrade_reasons)))
            ),
        )
        reproducibility_score = (
            differential_entry.robustness_score
            if differential_entry.robustness_score is not None
            else min(
                1.0,
                (
                    0.5
                    * score_support_count(
                        min(
                            differential_entry.observations_a,
                            differential_entry.observations_b,
                        ),
                        saturation=3,
                    )
                )
                + (
                    0.5
                    * score_support_count(
                        differential_entry.complete_pair_count,
                        saturation=3,
                    )
                ),
            )
        )
        qc_score = max(
            0.0,
            experiment_confidence_report.summary.overall_score
            - (0.04 * len(protein_card.warnings)),
        )
        penalties: dict[str, float] = {}
        if unique_support <= 1:
            penalties["single_peptide_support"] = 0.18
        if abundance_scores[protein_card.protein_group_id] < 0.25:
            penalties["low_abundance_signal"] = 0.12
        if protein_card.warnings:
            penalties["warning_burden"] = min(0.15, 0.03 * len(protein_card.warnings))
        if not protein_card.significant:
            penalties["not_significant"] = 0.1
        if differential_entry.imputation_dependent_hit:
            penalties["imputation_dependent_hit"] = 0.08
        if (
            differential_entry.robustness_score is not None
            and differential_entry.robustness_score < 0.5
        ):
            penalties["limited_robustness"] = 0.08
        candidates.append(
            EvidenceAwareRankingCandidate(
                candidate_id=protein_card.protein_group_id,
                entity_kind=EvidenceAwareRankingEntityKind.PROTEIN,
                display_label=protein_card.representative_protein_ref,
                effect_size=abs(protein_card.differential_result.log2_fold_change),
                adjusted_p_value=protein_card.differential_result.adjusted_p_value,
                abundance_value=abundance_value,
                support_count=unique_support,
                annotation_label=protein_card.annotation.gene_symbol
                or protein_card.annotation.description,
                effect_score=score_effect_size(
                    abs(protein_card.differential_result.log2_fold_change),
                    saturation=2.0,
                ),
                significance_score=score_adjusted_p_value(
                    protein_card.differential_result.adjusted_p_value
                ),
                abundance_score=abundance_scores[protein_card.protein_group_id],
                support_score=support_score,
                qc_score=qc_score,
                annotation_score=annotation_score,
                reproducibility_score=reproducibility_score,
                confidence_score=confidence_score,
                penalties=penalties,
                uncertainty=_biological_result_uncertainty(protein_card),
                source_ids=(
                    protein_card.card_id,
                    mechanism_card.card_id,
                    protein_card.graph_claim_node_id,
                ),
                note=(
                    "protein ranking combines differential strength, abundance, peptide "
                    "support, experiment confidence, annotation, and graph confidence"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_pathway_ranking_candidates(
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    if pathway_enrichment_report is None:
        return ()
    support_by_member_id: dict[str, list[float]] = {}
    abundance_by_member_id: dict[str, list[float]] = {}
    reproducibility_by_member_id: dict[str, list[float]] = {}
    for card in protein_mechanism_cards.cards:
        support_by_member_id.setdefault(card.protein_group_id, []).append(
            _tier_score(card.confidence_tier.value)
        )
        support_by_member_id.setdefault(card.representative_protein_ref, []).append(
            _tier_score(card.confidence_tier.value)
        )
        if card.gene_symbol:
            support_by_member_id.setdefault(card.gene_symbol, []).append(
                _tier_score(card.confidence_tier.value)
            )
        abundance = abs(card.abundance_change.log2_fold_change)
        abundance_by_member_id.setdefault(card.protein_group_id, []).append(abundance)
        abundance_by_member_id.setdefault(card.representative_protein_ref, []).append(
            abundance
        )
        if card.gene_symbol:
            abundance_by_member_id.setdefault(card.gene_symbol, []).append(abundance)
        reproducibility = min(
            1.0,
            (
                0.5
                * score_support_count(
                    card.peptide_support.unique_peptide_count,
                    saturation=4,
                )
            )
            + (0.5 * _tier_score(card.evidence_tier.value)),
        )
        reproducibility_by_member_id.setdefault(card.protein_group_id, []).append(
            reproducibility
        )
        reproducibility_by_member_id.setdefault(
            card.representative_protein_ref,
            [],
        ).append(reproducibility)
        if card.gene_symbol:
            reproducibility_by_member_id.setdefault(card.gene_symbol, []).append(
                reproducibility
            )

    pathway_abundance = {
        entry.pathway_id: _mean(
            abundance_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        for entry in pathway_enrichment_report.entries
    }
    abundance_scores = normalize_linear_range(pathway_abundance)

    candidates: list[EvidenceAwareRankingCandidate] = []
    for entry in pathway_enrichment_report.entries:
        support_strength = _mean(
            support_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        reproducibility = _mean(
            reproducibility_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        penalties: dict[str, float] = {}
        if entry.foreground_overlap_count <= 1:
            penalties["weak_member_support"] = 0.14
        if support_strength == 0.0:
            penalties["unresolved_supporting_members"] = 0.1
        if support_strength < 0.5:
            penalties["weak_supporting_proteins"] = 0.08
        candidates.append(
            EvidenceAwareRankingCandidate(
                candidate_id=entry.pathway_id,
                entity_kind=EvidenceAwareRankingEntityKind.PATHWAY,
                display_label=entry.pathway_name or entry.pathway_id,
                effect_size=entry.enrichment_ratio,
                adjusted_p_value=entry.adjusted_p_value,
                abundance_value=pathway_abundance[entry.pathway_id],
                support_count=entry.foreground_overlap_count,
                annotation_label=entry.source_name,
                effect_score=score_effect_size(
                    None
                    if entry.enrichment_ratio is None
                    else max(0.0, entry.enrichment_ratio - 1.0),
                    saturation=2.0,
                ),
                significance_score=score_adjusted_p_value(entry.adjusted_p_value),
                abundance_score=abundance_scores[entry.pathway_id],
                support_score=min(
                    1.0,
                    (
                        0.6
                        * score_support_count(
                            entry.foreground_overlap_count, saturation=5
                        )
                    )
                    + (0.4 * support_strength),
                ),
                qc_score=experiment_confidence_report.summary.overall_score,
                annotation_score=1.0
                if entry.pathway_name and entry.source_name
                else (0.75 if entry.pathway_name else 0.4),
                reproducibility_score=max(
                    0.4 * experiment_confidence_report.summary.overall_score,
                    reproducibility,
                ),
                confidence_score=support_strength,
                penalties=penalties,
                uncertainty=0.1 if support_strength == 0.0 else 0.05,
                source_ids=(entry.pathway_id,),
                note=(
                    "pathway ranking combines enrichment strength with supporting protein "
                    "confidence so one-member pathways do not outrank broader supported biology"
                ),
            )
        )
    return tuple(candidates)


def _mean(value_groups: Iterable[Sequence[float]]) -> float:
    values: list[float] = []
    for group in value_groups:
        values.extend(group)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _tier_score(value: str) -> float:
    return {
        "high": 1.0,
        "high_support": 1.0,
        "moderate": 0.72,
        "moderate_support": 0.72,
        "review": 0.45,
        "low": 0.3,
    }.get(value, 0.5)


def _biological_result_uncertainty(card: ProteinEvidenceCard) -> float:
    uncertainty = 0.0
    if card.differential_result.adjusted_p_value is None:
        uncertainty += 0.08
    if card.differential_result.uncertainty_note:
        uncertainty += 0.08
    if (
        min(
            card.differential_result.observations_a,
            card.differential_result.observations_b,
        )
        < 2
    ):
        uncertainty += 0.06
    return min(0.3, uncertainty)
