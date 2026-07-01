# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV renderers for targeted biomarker stability outputs."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.targeted.biomarker_stability.models import (
    BiomarkerStabilityReport,
)


def render_biomarker_stability_summary_tsv(report: BiomarkerStabilityReport) -> str:
    """Render biomarker stability summary as a stable TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(
        ("downgraded_candidate_count", report.summary.downgraded_candidate_count)
    )
    writer.writerow(
        (
            "low_reliable_sample_fraction_count",
            report.summary.low_reliable_sample_fraction_count,
        )
    )
    writer.writerow(
        (
            "single_condition_signal_only_count",
            report.summary.single_condition_signal_only_count,
        )
    )
    writer.writerow(
        (
            "batch_sensitive_candidate_count",
            report.summary.batch_sensitive_candidate_count,
        )
    )
    writer.writerow(
        (
            "timepoint_sensitive_candidate_count",
            report.summary.timepoint_sensitive_candidate_count,
        )
    )
    writer.writerow(
        (
            "sample_type_sensitive_candidate_count",
            report.summary.sample_type_sensitive_candidate_count,
        )
    )
    writer.writerow(
        (
            "assay_disagreement_candidate_count",
            report.summary.assay_disagreement_candidate_count,
        )
    )
    writer.writerow(
        (
            "sparse_subgroup_candidate_count",
            report.summary.sparse_subgroup_candidate_count,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_biomarker_stability_tsv(report: BiomarkerStabilityReport) -> str:
    """Render candidate-level biomarker stability outcomes as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "original_priority_rank",
            "adjusted_priority_rank",
            "original_final_score",
            "adjusted_final_score",
            "original_penalty_total",
            "adjusted_penalty_total",
            "stability_penalty",
            "stability_score",
            "reliable_sample_fraction",
            "condition_breadth_score",
            "assay_agreement_score",
            "batch_stability_score",
            "timepoint_stability_score",
            "sample_type_stability_score",
            "reliable_sample_count",
            "total_sample_count",
            "condition_count_with_signal",
            "total_condition_count",
            "assay_entry_count",
            "matched_target_count",
            "downgraded",
            "instability_reasons",
            "subgroup_behavior_count",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.original_priority_rank,
                entry.adjusted_priority_rank,
                _format_float(entry.original_final_score),
                _format_float(entry.adjusted_final_score),
                _format_float(entry.original_penalty_total),
                _format_float(entry.adjusted_penalty_total),
                _format_float(entry.stability_penalty),
                _format_float(entry.stability_score),
                _format_float(entry.reliable_sample_fraction),
                _format_float(entry.condition_breadth_score),
                _format_float(entry.assay_agreement_score),
                _format_float(entry.batch_stability_score),
                _format_float(entry.timepoint_stability_score),
                _format_float(entry.sample_type_stability_score),
                entry.reliable_sample_count,
                entry.total_sample_count,
                entry.condition_count_with_signal,
                entry.total_condition_count,
                entry.assay_entry_count,
                entry.matched_target_count,
                str(entry.downgraded).lower(),
                ";".join(reason.value for reason in entry.instability_reasons),
                entry.subgroup_behavior_count,
                entry.note,
            )
        )
    return handle.getvalue()


def render_biomarker_stability_subgroup_tsv(report: BiomarkerStabilityReport) -> str:
    """Render subgroup behavior behind biomarker stability calls as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "dimension",
            "subgroup_value",
            "reliable_sample_count",
            "total_sample_count",
            "mean_log2_intensity",
            "median_log2_intensity",
            "coefficient_of_variation",
            "residual_median_log2_intensity",
            "status",
            "note",
        )
    )
    for entry in report.subgroup_behavior:
        writer.writerow(
            (
                entry.candidate_id,
                entry.dimension.value,
                entry.subgroup_value,
                entry.reliable_sample_count,
                entry.total_sample_count,
                _format_float(entry.mean_log2_intensity),
                _format_float(entry.median_log2_intensity),
                _format_float(entry.coefficient_of_variation),
                _format_float(entry.residual_median_log2_intensity),
                entry.status.value,
                entry.note,
            )
        )
    return handle.getvalue()


def render_biomarker_stability_candidate_tsv(report: BiomarkerStabilityReport) -> str:
    """Render downgraded biomarker candidates in a downstream-usable TSV shape."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "penalty_total",
            "rank_reason_codes",
            "ranking_note",
            "original_priority_rank",
            "original_final_score",
            "stability_score",
            "stability_penalty",
            "downgraded",
            "instability_reasons",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.adjusted_priority_rank,
                _format_float(entry.adjusted_final_score),
                _format_float(entry.adjusted_penalty_total),
                ";".join(
                    sorted(
                        {
                            *(reason.value for reason in entry.instability_reasons),
                        }
                    )
                ),
                entry.note,
                entry.original_priority_rank,
                _format_float(entry.original_final_score),
                _format_float(entry.stability_score),
                _format_float(entry.stability_penalty),
                str(entry.downgraded).lower(),
                ";".join(reason.value for reason in entry.instability_reasons),
            )
        )
    return handle.getvalue()


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


__all__ = [
    "render_biomarker_stability_candidate_tsv",
    "render_biomarker_stability_subgroup_tsv",
    "render_biomarker_stability_summary_tsv",
    "render_biomarker_stability_tsv",
]
