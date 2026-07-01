# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed protein facade ledger for identification owner modules."""

from __future__ import annotations

from bijux_proteomics.identification.facade_ledger.models import (
    IdentificationFacadeBudget,
    IdentificationFacadeModule,
    build_facade_module,
)

PROTEIN_FACADE_BUDGET = IdentificationFacadeBudget(
    max_public_symbols=90,
    max_init_lines=80,
)


def list_identification_protein_api_modules() -> tuple[IdentificationFacadeModule, ...]:
    """Return the supported protein owner-facade modules."""

    return (
        build_facade_module(
            "bijux_proteomics.identification.protein.parsimony_review",
            "protein_review_owner",
            "Parsimony review owner surface.",
            (
                "ParsimonyReviewSummary",
                "ParsimonyReviewProteinEntry",
                "ParsimonyAmbiguityEntry",
                "ParsimonyReviewReport",
                "build_parsimony_review_report",
                "render_parsimony_review_summary_tsv",
                "render_parsimony_review_proteins_tsv",
                "render_parsimony_review_ambiguities_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_ambiguity_review",
            "protein_review_owner",
            "Protein ambiguity review owner surface.",
            (
                "ProteinAmbiguityReviewSummary",
                "ProteinAmbiguityReviewEntry",
                "ProteinAmbiguityReviewReport",
                "build_protein_ambiguity_review_report",
                "render_protein_ambiguity_summary_tsv",
                "render_protein_ambiguity_entries_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_coverage",
            "protein_coverage_owner",
            "Protein coverage owner surface.",
            (
                "ProteinCoverageCoordinateStatus",
                "ProteinCoverageSummary",
                "ProteinCoverageProteinEntry",
                "ProteinCoverageRegionEntry",
                "ProteinCoverageUncoveredRegionEntry",
                "ProteinCoveragePeptideCoordinateEntry",
                "ProteinCoverageReport",
                "build_protein_coverage_report",
                "render_protein_coverage_summary_tsv",
                "render_protein_coverage_entries_tsv",
                "render_protein_coverage_regions_tsv",
                "render_protein_coverage_uncovered_regions_tsv",
                "render_protein_coverage_peptide_coordinates_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_coverage_review",
            "protein_coverage_owner",
            "Protein coverage review owner surface.",
            (
                "ProteinCoverageReviewEntry",
                "ProteinCoverageReviewReport",
                "ProteinCoverageReviewSummary",
                "build_protein_coverage_review_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_coverage_visualization",
            "protein_visualization_owner",
            "Protein coverage visualization owner surface.",
            (
                "ProteinCoveragePlotEntry",
                "ProteinCoveragePlotTrack",
                "ProteinCoveragePlotUnmatchedEntry",
                "ProteinCoveragePlotSummary",
                "ProteinCoveragePlotReport",
                "build_protein_coverage_plot_report",
                "render_protein_coverage_plot_positions_tsv",
                "render_protein_coverage_plot_svg",
                "render_protein_coverage_plot_html",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_evidence",
            "protein_evidence_owner",
            "Protein evidence owner surface.",
            (
                "ProteinEvidenceTier",
                "ProteinEvidenceDowngradeReason",
                "ProteinEvidenceEntry",
                "ProteinEvidenceSummary",
                "ProteinEvidenceReport",
                "build_protein_evidence_report",
                "render_protein_evidence_summary_tsv",
                "render_protein_evidence_entries_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_evidence_review",
            "protein_evidence_owner",
            "Protein evidence review owner surface.",
            (
                "ProteinEvidenceReviewEntry",
                "ProteinEvidenceReviewReport",
                "ProteinEvidenceReviewSummary",
                "build_protein_evidence_review_report",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_grouping",
            "protein_grouping_owner",
            "Protein grouping owner surface.",
            (
                "ProteinGroupingSummary",
                "ProteinGroupingEntry",
                "ProteinGroupingReport",
                "build_protein_grouping_report",
                "render_protein_grouping_summary_tsv",
                "render_protein_grouping_entries_tsv",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_grouping_review",
            "protein_grouping_owner",
            "Protein grouping review owner surface.",
            ("build_protein_grouping_review_report",),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_inference_benchmarks",
            "protein_benchmark_owner",
            "Protein inference benchmark owner surface.",
            (
                "ProteinInferenceBenchmarkScenarioKind",
                "ProteinInferenceBenchmarkScenario",
                "ProteinInferenceMethodAssessment",
                "ProteinInferenceBenchmarkReport",
                "ProteinInferenceBenchmarkSuiteReport",
                "PickedGroupBenchmarkPressure",
                "PickedGroupFdrBenchmarkScenarioPlan",
                "PickedGroupFdrBenchmarkPlan",
                "WorkflowTrustCriterionResult",
                "IdentificationWorkflowClaimReview",
                "build_core_protein_inference_benchmark_scenarios",
                "build_protein_inference_benchmark_report",
                "build_protein_inference_benchmark_suite",
                "build_core_protein_inference_benchmark_suite",
                "render_protein_inference_benchmark_summary_tsv",
                "render_protein_inference_benchmark_scenarios_tsv",
                "render_protein_inference_benchmark_assessments_tsv",
                "build_picked_group_fdr_benchmark_plan",
                "build_identification_workflow_claim_review",
            ),
        ),
        build_facade_module(
            "bijux_proteomics.identification.protein.protein_parsimony",
            "protein_parsimony_owner",
            "Protein parsimony owner surface.",
            (
                "ProteinParsimonySummary",
                "ProteinParsimonyProteinEntry",
                "ProteinParsimonyAmbiguityEntry",
                "ProteinParsimonyReport",
                "build_protein_parsimony_report",
                "render_protein_parsimony_summary_tsv",
                "render_protein_parsimony_proteins_tsv",
                "render_protein_parsimony_ambiguities_tsv",
            ),
        ),
    )


__all__ = ["PROTEIN_FACADE_BUDGET", "list_identification_protein_api_modules"]
