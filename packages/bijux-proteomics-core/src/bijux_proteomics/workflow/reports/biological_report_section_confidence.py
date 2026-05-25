# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Biological report section confidence derivation."""

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
from bijux_proteomics.lab.protocol_context import (
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
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
    _BIOLOGICAL_REPORT_SECTION_TITLES,
)

def _build_section_confidence_entry(
    section_key: BiologicalReportSectionKey,
    confidence_label: BiologicalReportSectionConfidenceLabel,
    rationale: str,
) -> BiologicalReportSectionConfidenceEntry:
    return BiologicalReportSectionConfidenceEntry(
        section_key=section_key,
        section_title=_BIOLOGICAL_REPORT_SECTION_TITLES[section_key],
        confidence_label=confidence_label,
        rationale=rationale,
    )


def _build_biological_report_section_confidence_entries(
    *,
    experiment_confidence_report: ExperimentConfidenceReport,
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None,
    claim_validation_report: BiologicalClaimValidationReport | None,
    biological_hypothesis_report: BiologicalHypothesisReport | None,
    foreground_background_model: BiologicalForegroundBackgroundModel,
    regulator_inference_report: RegulatorInferenceReport | None,
    drug_target_report: DrugTargetInterpretationReport | None,
    disease_phenotype_report: DiseasePhenotypeInterpretationReport | None,
    cohort_stratification_report: CohortStratificationReport | None,
    tissue_cell_type_context_report: TissueCellTypeContextReport | None,
    compartment_biology_report: CompartmentBiologyReport | None,
    pathway_activity_report: PathwayActivityReport | None,
    complex_activity_report: ComplexActivityReport | None,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalReportSectionConfidenceEntry, ...]:
    entries: list[BiologicalReportSectionConfidenceEntry] = []
    summary = experiment_confidence_report.summary
    if summary.overall_tier.value == "high_confidence":
        if summary.low_confidence_component_count == 0:
            entries.append(
                _build_section_confidence_entry(
                    BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                    BiologicalReportSectionConfidenceLabel.HIGH,
                    "overall experimental confidence is high and no components were downgraded",
                )
            )
        else:
            entries.append(
                _build_section_confidence_entry(
                    BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                    BiologicalReportSectionConfidenceLabel.MODERATE,
                    "overall experimental confidence is high but at least one component remained low-confidence",
                )
            )
    elif summary.overall_tier.value == "moderate_confidence":
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                BiologicalReportSectionConfidenceLabel.MODERATE,
                "overall experimental confidence is moderate after aggregating metadata, missingness, power, and QC checks",
            )
        )
    else:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                BiologicalReportSectionConfidenceLabel.WEAK,
                "overall experimental confidence is low because multiple design or QC components were downgraded",
            )
        )

    if evidence_aware_ranking_report is None or not evidence_aware_ranking_report.entries:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no evidence-aware ranking entries were produced",
            )
        )
    else:
        top_score = evidence_aware_ranking_report.entries[0].decomposition.final_score
        if top_score >= 0.8:
            ranking_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif top_score >= 0.55:
            ranking_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            ranking_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING,
                ranking_label,
                f"ranking confidence derives from the top evidence-aware final score ({top_score:.3f}) across governed findings",
            )
        )

    if claim_validation_report is None or claim_validation_report.summary.candidate_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no biological claim candidates were available for validation",
            )
        )
    else:
        supported_count = claim_validation_report.summary.supported_claim_count
        candidate_count = claim_validation_report.summary.candidate_count
        support_fraction = supported_count / candidate_count
        if supported_count == 0:
            claim_label = BiologicalReportSectionConfidenceLabel.INVALID
            claim_rationale = "all candidate biological claims were rejected by directional or evidence checks"
        elif support_fraction >= 0.75 and claim_validation_report.summary.rejected_claim_count == 0:
            claim_label = BiologicalReportSectionConfidenceLabel.HIGH
            claim_rationale = (
                "most candidate biological claims remained supported and none were rejected"
            )
        elif support_fraction >= 0.4:
            claim_label = BiologicalReportSectionConfidenceLabel.MODERATE
            claim_rationale = (
                "supported biological claims remain after validation, but a material fraction were rejected"
            )
        else:
            claim_label = BiologicalReportSectionConfidenceLabel.WEAK
            claim_rationale = (
                "validated biological claims are sparse relative to the candidate claim set"
            )
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS,
                claim_label,
                claim_rationale,
            )
        )

    if (
        biological_hypothesis_report is None
        or biological_hypothesis_report.summary.candidate_count == 0
        or biological_hypothesis_report.summary.hypothesis_count == 0
    ):
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no graph-backed biological hypotheses were produced",
            )
        )
    else:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
                BiologicalReportSectionConfidenceLabel.EXPLORATORY,
                (
                    "hypotheses are intentionally exploratory follow-up statements, "
                    f"with {biological_hypothesis_report.summary.high_confidence_hypothesis_count} high-confidence hypotheses retained"
                ),
            )
        )

    if not foreground_background_model.summary.valid_for_enrichment:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "foreground/background construction failed the enrichment validity checks",
            )
        )
    else:
        issue_count = foreground_background_model.summary.issue_count
        if issue_count == 0:
            enrichment_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif issue_count == 1:
            enrichment_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            enrichment_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND,
                enrichment_label,
                (
                    "foreground/background confidence derives from enrichment validity and "
                    f"{issue_count} modeled issue(s)"
                ),
            )
        )

    if regulator_inference_report is None or regulator_inference_report.summary.entry_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.REGULATOR_INFERENCE,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no regulator entries were supported by the supplied evidence tables",
            )
        )
    else:
        high_scoring = regulator_inference_report.summary.high_scoring_entry_count
        unresolved_targets = regulator_inference_report.summary.unresolved_target_count
        if high_scoring > 0 and unresolved_targets == 0:
            regulator_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif high_scoring > 0:
            regulator_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            regulator_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.REGULATOR_INFERENCE,
                regulator_label,
                (
                    "regulator confidence derives from high-scoring inferred regulators and "
                    f"{unresolved_targets} unresolved target set(s)"
                ),
            )
        )

    if drug_target_report is None or drug_target_report.summary.entry_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no drug-target relationships were supported by explicit target annotations",
            )
        )
    else:
        summary = drug_target_report.summary
        if summary.high_evidence_entry_count > 0 and summary.direct_target_entry_count > 0:
            drug_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif summary.high_evidence_entry_count + summary.moderate_evidence_entry_count > 0:
            drug_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            drug_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
                drug_label,
                (
                    "drug-target confidence derives from explicit target evidence tiers and "
                    f"{summary.direct_target_entry_count} direct target entries"
                ),
            )
        )

    if disease_phenotype_report is None or disease_phenotype_report.summary.evaluated_term_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no disease or phenotype terms were evaluable from the supplied annotations",
            )
        )
    else:
        summary = disease_phenotype_report.summary
        if summary.high_confidence_term_count > 0 and summary.unknown_foreground_protein_count == 0:
            disease_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif summary.filter_passing_term_count > 0:
            disease_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            disease_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
                disease_label,
                (
                    "disease and phenotype confidence derives from passing-term counts and "
                    f"{summary.unknown_foreground_protein_count} unknown foreground proteins"
                ),
            )
        )

    if cohort_stratification_report is None or cohort_stratification_report.summary.supported_stratum_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COHORT_STRATIFICATION,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no supported subgroup strata passed the cohort stratification feasibility checks",
            )
        )
    else:
        summary = cohort_stratification_report.summary
        if summary.subgroup_effect_count > 0 or summary.interaction_candidate_count > 0:
            cohort_label = BiologicalReportSectionConfidenceLabel.EXPLORATORY
        else:
            cohort_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COHORT_STRATIFICATION,
                cohort_label,
                (
                    "cohort stratification confidence derives from supported subgroup strata and "
                    f"{summary.interaction_candidate_count} interaction candidate(s)"
                ),
            )
        )

    if (
        tissue_cell_type_context_report is None
        or tissue_cell_type_context_report.summary.sample_with_marker_definition_count == 0
    ):
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no samples carried marker definitions for tissue or cell-type validation",
            )
        )
    else:
        summary = tissue_cell_type_context_report.summary
        if summary.mismatch_warning_count > 0:
            tissue_label = BiologicalReportSectionConfidenceLabel.WEAK
        elif summary.insufficient_marker_support_count > 0:
            tissue_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            tissue_label = BiologicalReportSectionConfidenceLabel.HIGH
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
                tissue_label,
                (
                    "tissue and cell-type context confidence derives from sample marker agreement, "
                    f"{summary.mismatch_warning_count} mismatch warning(s), and "
                    f"{summary.insufficient_marker_support_count} insufficient-support sample(s)"
                ),
            )
        )

    if compartment_biology_report is None or compartment_biology_report.summary.compartment_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no compartments were evaluable from the supplied localization context",
            )
        )
    else:
        summary = compartment_biology_report.summary
        if (
            summary.condition_comparison_count > 0
            and summary.low_confidence_sample_score_count == 0
            and summary.unresolved_member_count == 0
            and summary.unknown_foreground_protein_count == 0
        ):
            compartment_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif summary.condition_comparison_count > 0:
            compartment_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            compartment_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
                compartment_label,
                (
                    "compartment confidence derives from condition comparisons, unresolved members, "
                    "and unknown-localization counts"
                ),
            )
        )

    if pathway_activity_report is None or pathway_activity_report.summary.pathway_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.PATHWAY_ACTIVITY,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no pathways were evaluable for activity scoring",
            )
        )
    else:
        summary = pathway_activity_report.summary
        if (
            summary.condition_comparison_count > 0
            and summary.low_confidence_sample_score_count == 0
            and summary.unresolved_member_count == 0
        ):
            pathway_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif summary.condition_comparison_count > 0:
            pathway_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            pathway_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.PATHWAY_ACTIVITY,
                pathway_label,
                (
                    "pathway activity confidence derives from pathway comparisons, "
                    f"{summary.low_confidence_sample_score_count} low-confidence sample score(s), "
                    f"and {summary.unresolved_member_count} unresolved member(s)"
                ),
            )
        )

    if complex_activity_report is None or complex_activity_report.summary.complex_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COMPLEX_ACTIVITY,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no complexes were evaluable for activity scoring",
            )
        )
    else:
        summary = complex_activity_report.summary
        if (
            summary.condition_comparison_count > 0
            and summary.low_confidence_sample_score_count == 0
            and summary.unresolved_member_count == 0
        ):
            complex_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif summary.condition_comparison_count > 0:
            complex_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            complex_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.COMPLEX_ACTIVITY,
                complex_label,
                (
                    "complex activity confidence derives from complex comparisons, "
                    f"{summary.low_confidence_sample_score_count} low-confidence sample score(s), "
                    f"and {summary.unresolved_member_count} unresolved member(s)"
                ),
            )
        )

    if protein_mechanism_cards.summary.card_count == 0:
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS,
                BiologicalReportSectionConfidenceLabel.INVALID,
                "no protein mechanism cards were generated",
            )
        )
    else:
        high_card_count = sum(
            1 for card in protein_mechanism_cards.cards if card.confidence_tier.value == "high"
        )
        moderate_card_count = sum(
            1
            for card in protein_mechanism_cards.cards
            if card.confidence_tier.value == "moderate"
        )
        if (
            high_card_count == protein_mechanism_cards.summary.card_count
            and protein_mechanism_cards.summary.weak_evidence_card_count == 0
        ):
            mechanism_label = BiologicalReportSectionConfidenceLabel.HIGH
        elif high_card_count + moderate_card_count > 0:
            mechanism_label = BiologicalReportSectionConfidenceLabel.MODERATE
        else:
            mechanism_label = BiologicalReportSectionConfidenceLabel.WEAK
        entries.append(
            _build_section_confidence_entry(
                BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS,
                mechanism_label,
                (
                    "protein mechanism card confidence derives from per-card propagated confidence tiers and "
                    f"{protein_mechanism_cards.summary.weak_evidence_card_count} weak-evidence card(s)"
                ),
            )
        )

    return tuple(entries)


def _count_section_confidence_labels(
    entries: tuple[BiologicalReportSectionConfidenceEntry, ...],
) -> dict[BiologicalReportSectionConfidenceLabel, int]:
    counts = {label: 0 for label in BiologicalReportSectionConfidenceLabel}
    for entry in entries:
        counts[entry.confidence_label] += 1
    return counts
