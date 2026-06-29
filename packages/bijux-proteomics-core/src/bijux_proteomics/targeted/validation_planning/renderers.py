# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV renderers for targeted validation experiment planning reports."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields

from .models import ValidationExperimentPlanningReport


def render_validation_experiment_planning_summary_tsv(
    report: ValidationExperimentPlanningReport,
) -> str:
    """Render validation planning summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(
        ("biomarker_candidate_count", report.summary.biomarker_candidate_count)
    )
    writer.writerow(("planned_target_count", report.summary.planned_target_count))
    writer.writerow(("planned_assay_count", report.summary.planned_assay_count))
    writer.writerow(("omitted_candidate_count", report.summary.omitted_candidate_count))
    writer.writerow(
        ("proposed_samples_per_group", report.summary.proposed_samples_per_group)
    )
    writer.writerow(
        (
            "recommended_panel_samples_per_group",
            report.summary.recommended_panel_samples_per_group,
        )
    )
    writer.writerow(
        ("underpowered_assay_count", report.summary.underpowered_assay_count)
    )
    writer.writerow(
        (
            "high_expected_missingness_assay_count",
            report.summary.high_expected_missingness_assay_count,
        )
    )
    writer.writerow(
        ("high_assay_risk_assay_count", report.summary.high_assay_risk_assay_count)
    )
    writer.writerow(
        ("pilot_backed_assay_count", report.summary.pilot_backed_assay_count)
    )
    writer.writerow(("heuristic_assay_count", report.summary.heuristic_assay_count))
    writer.writerow(("warning_count", report.summary.warning_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_validation_experiment_planning_plan_tsv(
    report: ValidationExperimentPlanningReport,
) -> str:
    """Render assay-level validation plan rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_display_label",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "uniqueness_score",
            "selected_transition_count",
            "exported_transition_count",
            "assay_interference_risk_tier",
            "assay_risk_score",
            "expected_missingness_fraction",
            "effect_size",
            "robustness_score",
            "pilot_pooled_log2_stddev",
            "pilot_observed_sample_count",
            "planning_mode",
            "proposed_samples_per_group",
            "recommended_minimum_samples_per_group",
            "underpowered",
            "warning_codes",
            "planning_note",
        )
    )
    for entry in sort_rows_by_fields(
        report.plan_entries, "biomarker_priority_rank", "assay_entry_id"
    ):
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.biomarker_candidate_id,
                entry.biomarker_candidate_kind.value,
                entry.biomarker_display_label,
                entry.biomarker_priority_rank,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.uniqueness_class.value,
                f"{entry.uniqueness_score:.6f}",
                entry.selected_transition_count,
                entry.exported_transition_count,
                entry.assay_interference_risk_tier.value,
                f"{entry.assay_risk_score:.6f}",
                f"{entry.expected_missingness_fraction:.6f}",
                "" if entry.effect_size is None else f"{entry.effect_size:.6f}",
                f"{entry.robustness_score:.6f}",
                ""
                if entry.pilot_pooled_log2_stddev is None
                else f"{entry.pilot_pooled_log2_stddev:.6f}",
                ""
                if entry.pilot_observed_sample_count is None
                else entry.pilot_observed_sample_count,
                entry.planning_mode.value,
                entry.proposed_samples_per_group,
                entry.recommended_minimum_samples_per_group,
                str(entry.underpowered).lower(),
                ";".join(code.value for code in entry.warning_codes),
                entry.planning_note,
            )
        )
    return handle.getvalue()


def render_validation_experiment_planning_warning_tsv(
    report: ValidationExperimentPlanningReport,
) -> str:
    """Render validation planning warnings as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "warning_id",
            "severity",
            "warning_code",
            "biomarker_candidate_id",
            "assay_entry_id",
            "target_protein_ref",
            "peptide_sequence",
            "message",
        )
    )
    for entry in sort_rows_by_fields(report.warnings, "warning_id"):
        writer.writerow(
            (
                entry.warning_id,
                entry.severity.value,
                entry.warning_code.value,
                entry.biomarker_candidate_id,
                "" if entry.assay_entry_id is None else entry.assay_entry_id,
                entry.target_protein_ref,
                "" if entry.peptide_sequence is None else entry.peptide_sequence,
                entry.message,
            )
        )
    return handle.getvalue()


__all__ = [
    "render_validation_experiment_planning_plan_tsv",
    "render_validation_experiment_planning_summary_tsv",
    "render_validation_experiment_planning_warning_tsv",
]
