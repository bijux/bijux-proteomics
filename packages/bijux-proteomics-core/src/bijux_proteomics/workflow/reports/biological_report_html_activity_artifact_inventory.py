# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Activity artifact inventory sections for biological report HTML."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
)


def _build_biological_activity_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    return [
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
    ]
