# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Owned summary construction for biological result report bundles."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _select_significant_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceLabel,
)
from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation import (
        BiologicalContextMappingReport,
        ComplexEnrichmentReport,
        GoEnrichmentReport,
        PathwayEnrichmentReport,
        ProteinAnnotationMappingReport,
        TissueCellTypeContextReport,
    )
    from bijux_proteomics.quantification.contracts import (
        DifferentialAbundanceReport,
        LabelFreeQuantTable,
    )
    from bijux_proteomics.quantification.provenance import (
        HeatmapPreparationReport,
        SampleExplorationReport,
    )
    from bijux_proteomics.study import ExperimentConfidenceReport
    from bijux_proteomics.workflow.cards.protein_evidence_cards import (
        ProteinEvidenceCardReport,
    )
    from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
        BiologicalResultSelectionPolicy,
    )
    from bijux_proteomics.workflow.studies.cohort_stratification import (
        CohortStratificationReport,
    )


def _build_biological_result_report_summary(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    selection_policy: BiologicalResultSelectionPolicy,
    annotation_report: ProteinAnnotationMappingReport,
    protein_cards: ProteinEvidenceCardReport,
    tissue_cell_type_context_report: TissueCellTypeContextReport | None,
    cohort_stratification_report: CohortStratificationReport | None,
    experiment_confidence_report: ExperimentConfidenceReport,
    section_confidence_counts: Mapping[BiologicalReportSectionConfidenceLabel, int],
    context_mapping_report: BiologicalContextMappingReport | None,
    go_enrichment_report: GoEnrichmentReport | None,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    complex_enrichment_report: ComplexEnrichmentReport | None,
    heatmap_report: HeatmapPreparationReport,
    sample_exploration_report: SampleExplorationReport,
) -> BiologicalResultReportSummary:
    return BiologicalResultReportSummary(
        protein_count=len(normalized_table.entity_ids),
        significant_protein_count=len(
            _select_significant_entity_ids(
                differential_report,
                policy=selection_policy,
            )
        ),
        sample_count=len(normalized_table.sample_ids),
        annotation_entry_count=len(annotation_report.result_entries),
        annotation_unmapped_count=len(annotation_report.unmapped_entries),
        protein_card_count=protein_cards.summary.protein_result_count,
        warning_card_count=protein_cards.summary.warning_card_count,
        tissue_mismatch_warning_count=(
            0
            if tissue_cell_type_context_report is None
            else tissue_cell_type_context_report.summary.mismatch_warning_count
        ),
        cohort_blocked_stratum_count=(
            0
            if cohort_stratification_report is None
            else cohort_stratification_report.summary.blocked_stratum_count
        ),
        cohort_subgroup_effect_count=(
            0
            if cohort_stratification_report is None
            else cohort_stratification_report.summary.subgroup_effect_count
        ),
        cohort_interaction_candidate_count=(
            0
            if cohort_stratification_report is None
            else cohort_stratification_report.summary.interaction_candidate_count
        ),
        experiment_confidence_score=experiment_confidence_report.summary.overall_score,
        experiment_confidence_tier=experiment_confidence_report.summary.overall_tier,
        low_confidence_component_count=(
            experiment_confidence_report.summary.low_confidence_component_count
        ),
        high_confidence_section_count=section_confidence_counts[
            BiologicalReportSectionConfidenceLabel.HIGH
        ],
        moderate_confidence_section_count=section_confidence_counts[
            BiologicalReportSectionConfidenceLabel.MODERATE
        ],
        weak_confidence_section_count=section_confidence_counts[
            BiologicalReportSectionConfidenceLabel.WEAK
        ],
        exploratory_section_count=section_confidence_counts[
            BiologicalReportSectionConfidenceLabel.EXPLORATORY
        ],
        invalid_section_count=section_confidence_counts[
            BiologicalReportSectionConfidenceLabel.INVALID
        ],
        context_entry_count=(
            0
            if context_mapping_report is None
            else len(context_mapping_report.mapped_entries)
        ),
        context_unmapped_count=(
            0
            if context_mapping_report is None
            else len(context_mapping_report.unmapped_entries)
        ),
        context_term_count=(
            0
            if context_mapping_report is None
            else len(context_mapping_report.term_entries)
        ),
        go_enriched_term_count=(
            0
            if go_enrichment_report is None
            else go_enrichment_report.summary.enriched_term_count
        ),
        pathway_enriched_entry_count=(
            0
            if pathway_enrichment_report is None
            else pathway_enrichment_report.summary.enriched_entry_count
        ),
        complex_enriched_entry_count=(
            0
            if complex_enrichment_report is None
            else complex_enrichment_report.summary.enriched_entry_count
        ),
        heatmap_entity_count=len(heatmap_report.rows),
        pca_outlier_sample_count=sum(
            1
            for entry in sample_exploration_report.sample_pca_report.entries
            if entry.outlier
        ),
    )
