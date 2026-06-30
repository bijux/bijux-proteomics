# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact inventory HTML."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
)


def _base_biological_report_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    return [
        ("Differential proteins", artifacts.differential_tsv),
        ("Protein card summary", artifacts.protein_card_summary_tsv),
        ("Protein cards", artifacts.protein_card_tsv),
        ("Pathway cards", artifacts.pathway_card_tsv),
        (
            "Protein mechanism card summary",
            artifacts.protein_mechanism_card_summary_tsv,
        ),
        ("Protein mechanism cards", artifacts.protein_mechanism_card_tsv),
        (
            "Experiment confidence summary",
            artifacts.experiment_confidence_summary_tsv,
        ),
        (
            "Experiment confidence components",
            artifacts.experiment_confidence_components_tsv,
        ),
        ("Report section confidence", artifacts.section_confidence_tsv),
        ("Evidence-aware ranking", artifacts.evidence_aware_ranking_tsv),
        ("Claim validation summary", artifacts.claim_validation_summary_tsv),
        ("Supported biological claims", artifacts.supported_claim_tsv),
        ("Rejected biological claims", artifacts.rejected_claim_tsv),
        (
            "Biological hypothesis summary",
            artifacts.biological_hypothesis_summary_tsv,
        ),
        ("Biological hypotheses", artifacts.biological_hypothesis_tsv),
        (
            "Rejected hypothesis candidates",
            artifacts.rejected_hypothesis_candidate_tsv,
        ),
        (
            "Enrichment foreground/background summary",
            artifacts.foreground_background_summary_tsv,
        ),
        (
            "Enrichment foreground/background entries",
            artifacts.foreground_background_entry_tsv,
        ),
        (
            "Enrichment foreground/background issues",
            artifacts.foreground_background_issue_tsv,
        ),
        (
            "Regulator inference summary",
            artifacts.regulator_inference_summary_tsv,
        ),
        ("Regulator inference", artifacts.regulator_inference_tsv),
        (
            "Regulator inference unresolved targets",
            artifacts.regulator_inference_unresolved_tsv,
        ),
        (
            "Regulator evidence rejected rows",
            artifacts.regulator_evidence_rejected_tsv,
        ),
        ("Annotation summary", artifacts.annotation_summary_tsv),
        ("Annotated proteins", artifacts.annotation_tsv),
        ("Unmapped annotations", artifacts.annotation_unmapped_tsv),
        ("Biological context summary", artifacts.context_summary_tsv),
        ("Biological context mappings", artifacts.context_mapping_tsv),
        ("Biological context terms", artifacts.context_term_tsv),
        ("Biological context unmapped", artifacts.context_unmapped_tsv),
        ("Biological context rejected rows", artifacts.context_rejected_tsv),
        (
            "Cohort stratification summary",
            artifacts.cohort_stratification_summary_tsv,
        ),
        ("Cohort strata", artifacts.cohort_stratum_tsv),
        ("Cohort subgroup effects", artifacts.cohort_subgroup_effect_tsv),
        (
            "Cohort interaction candidates",
            artifacts.cohort_interaction_candidate_tsv,
        ),
        (
            "Tissue and cell-type context summary",
            artifacts.tissue_context_summary_tsv,
        ),
        (
            "Tissue and cell-type sample consistency",
            artifacts.tissue_context_sample_consistency_tsv,
        ),
        (
            "Tissue and cell-type unexpected signals",
            artifacts.tissue_context_unexpected_signal_tsv,
        ),
        (
            "Tissue and cell-type interpretations",
            artifacts.tissue_context_interpretation_tsv,
        ),
        (
            "Compartment biology summary",
            artifacts.compartment_biology_summary_tsv,
        ),
        ("Compartment enrichment", artifacts.compartment_enrichment_tsv),
        (
            "Compartment activity matrix",
            artifacts.compartment_activity_matrix_tsv,
        ),
        (
            "Compartment activity sample scores",
            artifacts.compartment_activity_sample_score_tsv,
        ),
        (
            "Compartment activity condition scores",
            artifacts.compartment_activity_condition_score_tsv,
        ),
        (
            "Compartment activity condition comparisons",
            artifacts.compartment_activity_condition_comparison_tsv,
        ),
        (
            "Compartment activity unresolved members",
            artifacts.compartment_activity_unresolved_member_tsv,
        ),
        (
            "Compartment unknown localization",
            artifacts.compartment_unknown_localization_tsv,
        ),
        ("Pathway activity summary", artifacts.pathway_activity_summary_tsv),
        ("Pathway activity matrix", artifacts.pathway_activity_matrix_tsv),
        (
            "Pathway activity sample scores",
            artifacts.pathway_activity_sample_score_tsv,
        ),
        (
            "Pathway activity condition scores",
            artifacts.pathway_activity_condition_score_tsv,
        ),
        (
            "Pathway activity condition comparisons",
            artifacts.pathway_activity_condition_comparison_tsv,
        ),
        (
            "Pathway activity member contributions",
            artifacts.pathway_activity_member_contribution_tsv,
        ),
        (
            "Pathway activity unresolved members",
            artifacts.pathway_activity_unresolved_member_tsv,
        ),
        ("Sample cards", artifacts.sample_card_tsv),
        ("Complex activity summary", artifacts.complex_activity_summary_tsv),
        ("Complex activity matrix", artifacts.complex_activity_matrix_tsv),
        (
            "Complex activity sample scores",
            artifacts.complex_activity_sample_score_tsv,
        ),
        (
            "Complex activity condition scores",
            artifacts.complex_activity_condition_score_tsv,
        ),
        (
            "Complex activity condition comparisons",
            artifacts.complex_activity_condition_comparison_tsv,
        ),
        (
            "Complex activity member contributions",
            artifacts.complex_activity_member_contribution_tsv,
        ),
        (
            "Complex activity unresolved members",
            artifacts.complex_activity_unresolved_member_tsv,
        ),
        ("Volcano TSV", artifacts.volcano_tsv),
        ("Volcano JSON", artifacts.volcano_json),
        ("Volcano SVG", artifacts.volcano_svg),
        ("Volcano HTML", artifacts.volcano_html),
        ("Heatmap summary", artifacts.heatmap_summary_tsv),
        ("Heatmap matrix", artifacts.heatmap_matrix_tsv),
        ("Sample PCA scores", artifacts.sample_pca_scores_tsv),
        ("Sample distances", artifacts.sample_distance_tsv),
        ("Sample clusters", artifacts.sample_cluster_tsv),
    ]


def _optional_biological_report_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    sections: list[tuple[str, str | None]] = []
    if artifacts.go_term_tsv is not None:
        sections.append(("GO enrichment", artifacts.go_term_tsv))
    if artifacts.pathway_entry_tsv is not None:
        sections.append(("Pathway enrichment", artifacts.pathway_entry_tsv))
    if artifacts.complex_entry_tsv is not None:
        sections.append(("Complex enrichment", artifacts.complex_entry_tsv))
    if artifacts.drug_target_tsv is not None:
        sections.append(("Drug-target interpretation", artifacts.drug_target_tsv))
    if artifacts.disease_phenotype_term_tsv is not None:
        sections.append(
            (
                "Disease and phenotype interpretation",
                artifacts.disease_phenotype_term_tsv,
            )
        )
    return sections


def _render_biological_report_artifact_inventory_html(
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = _base_biological_report_artifact_sections(
        artifacts
    ) + _optional_biological_report_artifact_sections(artifacts)
    return "".join(
        f"<li><strong>{escape(label)}</strong>: <code>{escape(path)}</code></li>"
        for label, path in sections
        if path is not None
    )


__all__ = ["_render_biological_report_artifact_inventory_html"]
