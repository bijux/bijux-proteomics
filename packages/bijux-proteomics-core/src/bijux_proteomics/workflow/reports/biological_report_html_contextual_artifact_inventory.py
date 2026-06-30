# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contextual artifact inventory sections for biological report HTML."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)


def _build_biological_contextual_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    return [
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
        ("Drug-target interpretation", artifacts.drug_target_tsv),
        (
            "Disease and phenotype interpretation",
            artifacts.disease_phenotype_term_tsv,
        ),
    ]
