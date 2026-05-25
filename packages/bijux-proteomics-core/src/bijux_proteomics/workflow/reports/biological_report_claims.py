# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Biological claim and hypothesis construction helpers."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from bijux_proteomics.interpretation import (
    BiologicalContextKind,
    BiologicalContextImportReport,
    BiologicalContextMappingReport,
    BiologicalForegroundBackgroundModel,
    BiologicalSetEntry,
    BiologicalSetFilteringPolicy,
    BiologicalSetSourceKind,
    ComplexActivityReport,
    ComplexEnrichmentCorrectionPolicy,
    ComplexEnrichmentReport,
    DrugTargetInterpretationPolicy,
    DrugTargetInterpretationReport,
    DiseasePhenotypeInterpretationPolicy,
    DiseasePhenotypeInterpretationReport,
    build_complex_activity_report,
    build_biological_context_mapping_report,
    build_biological_foreground_background_model,
    build_drug_target_interpretation_report,
    build_disease_phenotype_interpretation_report,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_member_contribution_tsv,
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_unresolved_member_tsv,
    render_drug_target_interpretation_summary_tsv,
    render_drug_target_interpretation_tsv,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
    PathwayEnrichmentCorrectionPolicy,
    PathwayEnrichmentReport,
    PathwayActivityReport,
    GoEnrichmentCorrectionPolicy,
    GoEnrichmentReport,
    ProteinAnnotationColumnMapping,
    ProteinAnnotationMappingReport,
    ProteinReferenceEntry,
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    apply_complex_enrichment_multiple_testing,
    apply_go_enrichment_multiple_testing,
    apply_pathway_enrichment_multiple_testing,
    build_complex_enrichment_report,
    build_go_enrichment_report,
    build_pathway_activity_report,
    build_pathway_enrichment_report,
    build_protein_annotation_mapping_report,
    build_regulator_inference_report,
    build_regulator_site_signal_entries_from_ptm_evidence_cards,
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
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
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
    render_protein_annotation_tsv,
    render_protein_annotation_summary_tsv,
    render_rejected_regulator_evidence_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_tissue_cell_type_context_summary_tsv,
    render_tissue_cell_type_interpretation_tsv,
    render_tissue_cell_type_sample_consistency_tsv,
    render_tissue_cell_type_unexpected_signal_tsv,
    render_unresolved_regulator_target_tsv,
    render_unmapped_protein_annotation_tsv,
    require_valid_biological_foreground_background_model,
    TissueCellTypeContextReport,
    build_tissue_cell_type_context_report,
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
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_sample_cluster_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    Ms1FeatureColumnMapping,
    LabelFreeQuantTable,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    SampleExplorationReport,
    build_differential_abundance_report,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_missingness_condition_summary_report,
    build_power_estimation_report,
    build_sample_exploration_report,
    normalize_label_free_table,
    parse_ms1_feature_table,
    render_differential_abundance_tsv,
)
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.quantification.differential_abundance import (
    apply_benjamini_hochberg,
)
from bijux_proteomics.review import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
    BiologicalHypothesisReport,
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    EvidenceAwareRankingReport,
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_biological_claim_validation_report,
    build_biological_hypothesis_report,
    build_evidence_aware_ranking_report,
    build_quantification_volcano_review,
    export_proteomics_evidence_graph,
    export_volcano_review_html,
    normalize_linear_range,
    export_volcano_review_json,
    export_volcano_review_svg,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
    render_biological_claim_validation_summary_tsv,
    render_biological_hypothesis_summary_tsv,
    render_biological_hypothesis_tsv,
    render_rejected_biological_hypothesis_candidate_tsv,
    render_rejected_biological_claim_tsv,
    render_supported_biological_claim_tsv,
    render_volcano_review_tsv,
    render_evidence_aware_ranking_tsv,
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_proteogenomic_variant_peptide_table,
    parse_protein_region_context_tsv,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
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
from bijux_proteomics.study.lab_protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
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
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
    build_biological_result_graph_report,
)
from bijux_proteomics.workflow.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
    render_cohort_interaction_candidate_tsv,
    render_cohort_stratification_summary_tsv,
    render_cohort_stratum_tsv,
    render_cohort_subgroup_effect_tsv,
)
from bijux_proteomics_foundation import JsonModel

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.reports.biological_report_ranking import (
    _build_biological_pathway_ranking_candidates,
    _build_biological_protein_ranking_candidates,
)

def _build_biological_evidence_aware_ranking_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
) -> EvidenceAwareRankingReport:
    protein_candidates = _build_biological_protein_ranking_candidates(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    pathway_candidates = _build_biological_pathway_ranking_candidates(
        pathway_enrichment_report,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    return build_evidence_aware_ranking_report(
        protein_candidates + pathway_candidates
    )


def _build_biological_claim_validation_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalClaimValidationReport:
    candidates = (
        _build_biological_protein_claim_candidates(
            differential_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_claim_candidates(pathway_activity_report)
        + _build_biological_regulator_claim_candidates(regulator_inference_report)
    )
    return build_biological_claim_validation_report(
        candidates,
        policy=BiologicalClaimValidationPolicy(
            max_adjusted_p_value=selection_policy.max_adjusted_p_value,
            min_robustness_score=0.55,
            min_pathway_activity_delta=0.2,
            min_regulator_score=0.55,
        ),
    )


def _build_biological_hypothesis_report(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> BiologicalHypothesisReport:
    candidates = (
        _build_biological_protein_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            pathway_activity_report=pathway_activity_report,
        )
        + _build_biological_regulator_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            regulator_inference_report=regulator_inference_report,
        )
    )
    return build_biological_hypothesis_report(candidates)


def _build_biological_protein_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    cards_by_group_id = {
        card.protein_group_id: card for card in protein_mechanism_cards.cards
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE:
            continue
        card = cards_by_group_id.get(claim.subject_id)
        supporting_site_keys = (
            tuple(ptm.site_key for ptm in card.ptms) if card is not None else ()
        )
        supporting_pathway_ids = (
            tuple(pathway.entry_id for pathway in card.pathways)
            if card is not None
            else ()
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=f"protein-hypothesis:{claim.subject_id}",
                hypothesis_kind=BiologicalHypothesisKind.PROTEIN_MECHANISM,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=(
                    (card.representative_protein_ref,) if card is not None else ()
                ),
                supporting_site_keys=supporting_site_keys,
                supporting_pathway_ids=supporting_pathway_ids,
                opposing_evidence=(
                    _protein_hypothesis_opposing_evidence(card) if card is not None else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(
                    () if card is None else (card,)
                ),
                base_confidence_score=_protein_hypothesis_base_confidence(claim, card=card),
                source_ids=claim.source_ids
                + (() if card is None else (card.card_id, card.protein_card_id)),
                note=(
                    "validated protein claims become biological hypotheses only when a "
                    "graph-backed protein mechanism card preserves the supporting claim "
                    "and subject node ids"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_pathway_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if pathway_activity_report is None:
        return ()
    cards_by_ref = {
        card.representative_protein_ref: card for card in protein_mechanism_cards.cards
    }
    comparisons = {
        (entry.pathway_id, entry.condition_a, entry.condition_b): entry
        for entry in pathway_activity_report.condition_comparisons
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE:
            continue
        comparison = comparisons.get((claim.subject_id, claim.condition_a, claim.condition_b))
        supporting_protein_refs = (
            ()
            if comparison is None
            else _pathway_hypothesis_supporting_protein_refs(
                pathway_activity_report,
                pathway_id=comparison.pathway_id,
                condition_a=comparison.condition_a,
                condition_b=comparison.condition_b,
                cards_by_ref=cards_by_ref,
            )
        )
        supporting_cards = tuple(
            cards_by_ref[protein_ref]
            for protein_ref in supporting_protein_refs
            if protein_ref in cards_by_ref
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=(
                    "pathway-hypothesis:"
                    f"{claim.subject_id}:{claim.condition_a}:{claim.condition_b}"
                ),
                hypothesis_kind=BiologicalHypothesisKind.PATHWAY_ACTIVITY,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=supporting_protein_refs,
                supporting_pathway_ids=(claim.subject_id,),
                opposing_evidence=(
                    _pathway_hypothesis_opposing_evidence(
                        pathway_activity_report,
                        comparison=comparison,
                    )
                    if comparison is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(supporting_cards),
                base_confidence_score=_pathway_hypothesis_base_confidence(
                    claim,
                    comparison=comparison,
                ),
                source_ids=claim.source_ids
                + tuple(card.card_id for card in supporting_cards),
                note=(
                    "pathway hypotheses inherit directional activity support from the "
                    "owned pathway activity report and anchor onto graph-backed member "
                    "protein evidence nodes"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_regulator_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if regulator_inference_report is None:
        return ()
    cards_by_ref = {
        card.representative_protein_ref: card for card in protein_mechanism_cards.cards
    }
    entries_by_claim_id = {
        (
            "regulator-claim:"
            f"{entry.regulator}:{entry.evidence_type.value}:{entry.signal_surface.value}"
        ): entry
        for entry in regulator_inference_report.entries
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.REGULATOR_ACTIVITY:
            continue
        regulator_entry = entries_by_claim_id.get(claim.claim_id)
        supporting_protein_refs = (
            ()
            if regulator_entry is None
            else tuple(
                protein_ref
                for protein_ref in regulator_entry.supporting_protein_refs
                if protein_ref in cards_by_ref
            )
        )
        supporting_cards = tuple(
            cards_by_ref[protein_ref]
            for protein_ref in supporting_protein_refs
            if protein_ref in cards_by_ref
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=f"regulator-hypothesis:{claim.subject_id}",
                hypothesis_kind=BiologicalHypothesisKind.REGULATOR_ACTIVITY,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=supporting_protein_refs,
                supporting_site_keys=(
                    () if regulator_entry is None else regulator_entry.supporting_site_keys
                ),
                supporting_pathway_ids=(
                    ()
                    if regulator_entry is None
                    else regulator_entry.supporting_pathway_ids
                ),
                opposing_evidence=(
                    _regulator_hypothesis_opposing_evidence(
                        regulator_inference_report,
                        regulator=claim.subject_id,
                    )
                    if regulator_entry is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(supporting_cards),
                base_confidence_score=_regulator_hypothesis_base_confidence(
                    claim,
                    regulator_score=(
                        None if regulator_entry is None else regulator_entry.score
                    ),
                ),
                source_ids=claim.source_ids
                + tuple(card.card_id for card in supporting_cards),
                note=(
                    "regulator hypotheses preserve the explicit downstream signal "
                    "surface and anchor onto graph-backed supporting protein evidence"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_protein_claim_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalClaimCandidate, ...]:
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    candidates: list[BiologicalClaimCandidate] = []
    for card in protein_mechanism_cards.cards:
        if card.abundance_change.direction.value == "unchanged":
            continue
        differential_entry = differential_by_entity.get(card.protein_group_id)
        if differential_entry is None:
            raise ValueError(
                "biological claim validation requires one differential entry per protein mechanism card"
            )
        direction = (
            BiologicalClaimDirection.UP
            if card.abundance_change.direction.value == "increased"
            else BiologicalClaimDirection.DOWN
        )
        direction_label = "increased" if direction is BiologicalClaimDirection.UP else "decreased"
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=f"protein-claim:{card.protein_group_id}",
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id=card.protein_group_id,
                subject_label=card.gene_symbol or card.representative_protein_ref,
                claim_text=(
                    f"Protein {card.gene_symbol or card.representative_protein_ref} "
                    f"{direction_label} in {card.abundance_change.condition_b} vs "
                    f"{card.abundance_change.condition_a}"
                ),
                condition_a=card.abundance_change.condition_a,
                condition_b=card.abundance_change.condition_b,
                asserted_direction=direction,
                significant=card.abundance_change.significant,
                adjusted_p_value=card.abundance_change.adjusted_p_value,
                effect_size=abs(card.abundance_change.log2_fold_change),
                robustness_score=differential_entry.robustness_score,
                imputation_dependent=differential_entry.imputation_dependent_hit,
                evidence_tier=card.evidence_tier,
                confidence_tier=card.confidence_tier,
                source_ids=(
                    card.card_id,
                    card.graph_claim_node_id,
                    card.protein_card_id,
                ),
                note=(
                    "protein abundance claims require robust quantitative support, "
                    "not just nominal differential direction"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_pathway_claim_candidates(
    pathway_activity_report: PathwayActivityReport | None,
) -> tuple[BiologicalClaimCandidate, ...]:
    if pathway_activity_report is None:
        return ()
    candidates: list[BiologicalClaimCandidate] = []
    for entry in pathway_activity_report.condition_comparisons:
        if entry.activity_score_delta is None or entry.activity_score_delta == 0.0:
            continue
        direction = (
            BiologicalClaimDirection.UP
            if entry.activity_score_delta > 0.0
            else BiologicalClaimDirection.DOWN
        )
        verb = "activated" if direction is BiologicalClaimDirection.UP else "suppressed"
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=(
                    "pathway-claim:"
                    f"{entry.pathway_id}:{entry.condition_a}:{entry.condition_b}"
                ),
                claim_kind=BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE,
                subject_id=entry.pathway_id,
                subject_label=entry.pathway_name or entry.pathway_id,
                claim_text=(
                    f"Pathway {entry.pathway_name or entry.pathway_id} {verb} in "
                    f"{entry.condition_b} vs {entry.condition_a}"
                ),
                condition_a=entry.condition_a,
                condition_b=entry.condition_b,
                asserted_direction=direction,
                effect_size=abs(entry.activity_score_delta),
                pathway_confidence_status=entry.comparison_confidence_status.value,
                pathway_delta=entry.activity_score_delta,
                source_ids=(
                    f"pathway-activity:{entry.pathway_id}",
                    f"pathway-activity-comparison:{entry.pathway_id}:{entry.condition_a}:{entry.condition_b}",
                ),
                note=(
                    "pathway activation claims require explicit directional activity "
                    "deltas with high-confidence comparison support"
                ),
            )
        )
    return tuple(candidates)


def _build_biological_regulator_claim_candidates(
    regulator_inference_report: RegulatorInferenceReport | None,
) -> tuple[BiologicalClaimCandidate, ...]:
    if regulator_inference_report is None:
        return ()
    candidates: list[BiologicalClaimCandidate] = []
    for entry in regulator_inference_report.entries:
        direction = {
            "up": BiologicalClaimDirection.UP,
            "down": BiologicalClaimDirection.DOWN,
            "mixed": BiologicalClaimDirection.MIXED,
            "unsupported": BiologicalClaimDirection.UNRESOLVED,
        }[entry.direction.value]
        if entry.evidence_type.value == "kinase_substrate":
            noun = "Kinase"
            verb = (
                "active"
                if direction is BiologicalClaimDirection.UP
                else (
                    "suppressed"
                    if direction is BiologicalClaimDirection.DOWN
                    else "unresolved"
                )
            )
        else:
            noun = "Regulator"
            verb = (
                "active"
                if direction is BiologicalClaimDirection.UP
                else (
                    "suppressed"
                    if direction is BiologicalClaimDirection.DOWN
                    else "unresolved"
                )
            )
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=(
                    "regulator-claim:"
                    f"{entry.regulator}:{entry.evidence_type.value}:{entry.signal_surface.value}"
                ),
                claim_kind=BiologicalClaimKind.REGULATOR_ACTIVITY,
                subject_id=entry.regulator,
                subject_label=entry.regulator,
                claim_text=(
                    f"{noun} {entry.regulator} {verb} in "
                    f"{regulator_inference_report.condition_b} vs "
                    f"{regulator_inference_report.condition_a}"
                ),
                condition_a=regulator_inference_report.condition_a,
                condition_b=regulator_inference_report.condition_b,
                asserted_direction=direction,
                effect_size=abs(
                    entry.mean_log2_fold_change
                    if entry.mean_log2_fold_change is not None
                    else (entry.mean_activity_score_delta or 0.0)
                ),
                regulator_evidence_type=entry.evidence_type.value,
                regulator_signal_surface=entry.signal_surface.value,
                regulator_score=entry.score,
                source_ids=(
                    f"regulator-inference:{entry.regulator}",
                    f"regulator-surface:{entry.signal_surface.value}",
                ),
                note=(
                    "regulator claims require directional downstream support on the "
                    "appropriate evidence surface"
                ),
            )
        )
    return tuple(candidates)


def _graph_node_ids_from_cards(cards: tuple[ProteinMechanismCard, ...]) -> tuple[str, ...]:
    node_ids: list[str] = []
    for card in cards:
        node_ids.extend((card.graph_subject_node_id, card.graph_claim_node_id))
    return tuple(sorted(set(node_ids)))


def _protein_hypothesis_base_confidence(
    claim,
    *,
    card: ProteinMechanismCard | None,
) -> float:
    component_scores = [
        claim.robustness_score if claim.robustness_score is not None else 0.55,
        _evidence_tier_score(None if card is None else card.evidence_tier),
        _confidence_tier_score(None if card is None else card.confidence_tier.value),
    ]
    return round(sum(component_scores) / len(component_scores), 3)


def _pathway_hypothesis_base_confidence(
    claim,
    *,
    comparison,
) -> float:
    delta_score = min(1.0, abs(claim.pathway_delta or 0.0) / 1.0)
    comparison_score = _pathway_confidence_score(
        None if comparison is None else comparison.comparison_confidence_status.value
    )
    return round((delta_score + comparison_score) / 2.0, 3)


def _regulator_hypothesis_base_confidence(
    claim,
    *,
    regulator_score: float | None,
) -> float:
    score = regulator_score if regulator_score is not None else claim.regulator_score
    if score is None:
        return 0.55
    return round(score, 3)


def _evidence_tier_score(evidence_tier) -> float:
    if evidence_tier is None:
        return 0.55
    if evidence_tier.value == "high_confidence":
        return 0.9
    if evidence_tier.value == "moderate_confidence":
        return 0.7
    return 0.55


def _confidence_tier_score(confidence_tier: str | None) -> float:
    if confidence_tier == "high":
        return 0.9
    if confidence_tier == "moderate":
        return 0.7
    return 0.55


def _pathway_confidence_score(confidence_status: str | None) -> float:
    if confidence_status == "high_confidence":
        return 0.85
    return 0.55


def _protein_hypothesis_opposing_evidence(
    card: ProteinMechanismCard,
) -> tuple[str, ...]:
    opposing = {
        *(reason.value for reason in card.downgrade_reasons),
        *(code.value for code in card.warning_codes),
    }
    return tuple(sorted(opposing))


def _pathway_hypothesis_supporting_protein_refs(
    pathway_activity_report: PathwayActivityReport,
    *,
    pathway_id: str,
    condition_a: str,
    condition_b: str,
    cards_by_ref: dict[str, ProteinMechanismCard],
) -> tuple[str, ...]:
    supporting_refs = {
        protein_ref
        for contribution in pathway_activity_report.member_contributions
        if contribution.pathway_id == pathway_id
        and contribution.observed
        and contribution.condition in {condition_a, condition_b}
        for protein_ref in contribution.observed_protein_refs
        if protein_ref in cards_by_ref
    }
    return tuple(sorted(supporting_refs))


def _pathway_hypothesis_opposing_evidence(
    pathway_activity_report: PathwayActivityReport,
    *,
    comparison,
) -> tuple[str, ...]:
    unresolved_member_ids = {
        unresolved.member_id
        for unresolved in pathway_activity_report.unresolved_members
        if unresolved.pathway_id == comparison.pathway_id
    }
    opposing_evidence = {
        (
            "low_confidence_pathway_comparison"
            if comparison.comparison_confidence_status.value != "high_confidence"
            else ""
        ),
        *(
            f"unresolved pathway member {member_id}"
            for member_id in sorted(unresolved_member_ids)
        ),
    }
    return tuple(sorted(item for item in opposing_evidence if item))


def _regulator_hypothesis_opposing_evidence(
    regulator_inference_report: RegulatorInferenceReport,
    *,
    regulator: str,
) -> tuple[str, ...]:
    unresolved_targets = {
        entry.target_value
        for entry in regulator_inference_report.unresolved_targets
        if entry.regulator == regulator
    }
    return tuple(
        sorted(
            f"unresolved regulator target {target_value}"
            for target_value in unresolved_targets
        )
    )
