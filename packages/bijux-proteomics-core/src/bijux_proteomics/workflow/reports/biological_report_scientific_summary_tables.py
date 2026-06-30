# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned TSV summary tables for biological scientific report exports."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def render_biological_result_report_summary_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    """Render one biological result report summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("condition_a", report.volcano_review.condition_a))
    writer.writerow(("condition_b", report.volcano_review.condition_b))
    writer.writerow(("protein_count", report.summary.protein_count))
    writer.writerow(
        ("significant_protein_count", report.summary.significant_protein_count)
    )
    writer.writerow(("sample_count", report.summary.sample_count))
    writer.writerow(("annotation_entry_count", report.summary.annotation_entry_count))
    writer.writerow(
        ("annotation_unmapped_count", report.summary.annotation_unmapped_count)
    )
    writer.writerow(("protein_card_count", report.summary.protein_card_count))
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        ("tissue_mismatch_warning_count", report.summary.tissue_mismatch_warning_count)
    )
    writer.writerow(
        ("cohort_blocked_stratum_count", report.summary.cohort_blocked_stratum_count)
    )
    writer.writerow(
        (
            "cohort_subgroup_effect_count",
            report.summary.cohort_subgroup_effect_count,
        )
    )
    writer.writerow(
        (
            "cohort_interaction_candidate_count",
            report.summary.cohort_interaction_candidate_count,
        )
    )
    writer.writerow(
        (
            "experiment_confidence_score",
            f"{report.summary.experiment_confidence_score:.4f}",
        )
    )
    writer.writerow(
        ("experiment_confidence_tier", report.summary.experiment_confidence_tier)
    )
    writer.writerow(
        (
            "low_confidence_component_count",
            report.summary.low_confidence_component_count,
        )
    )
    writer.writerow(
        (
            "high_confidence_section_count",
            report.summary.high_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "moderate_confidence_section_count",
            report.summary.moderate_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "weak_confidence_section_count",
            report.summary.weak_confidence_section_count,
        )
    )
    writer.writerow(
        (
            "exploratory_section_count",
            report.summary.exploratory_section_count,
        )
    )
    writer.writerow(
        (
            "invalid_section_count",
            report.summary.invalid_section_count,
        )
    )
    writer.writerow(("context_entry_count", report.summary.context_entry_count))
    writer.writerow(("context_unmapped_count", report.summary.context_unmapped_count))
    writer.writerow(("context_term_count", report.summary.context_term_count))
    writer.writerow(("go_enriched_term_count", report.summary.go_enriched_term_count))
    writer.writerow(
        ("pathway_enriched_entry_count", report.summary.pathway_enriched_entry_count)
    )
    writer.writerow(
        ("complex_enriched_entry_count", report.summary.complex_enriched_entry_count)
    )
    writer.writerow(("heatmap_entity_count", report.summary.heatmap_entity_count))
    writer.writerow(
        ("pca_outlier_sample_count", report.summary.pca_outlier_sample_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_biological_report_section_confidence_tsv(
    report: BiologicalResultReportBundle,
) -> str:
    """Render derived biological report section confidence labels as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("section_key", "section_title", "confidence_label", "rationale"))
    for entry in report.section_confidence_entries:
        writer.writerow(
            (
                entry.section_key.value,
                entry.section_title,
                entry.confidence_label.value,
                entry.rationale,
            )
        )
    return handle.getvalue()
