# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable tabular rendering for regulator inference outputs."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.interpretation.regulator_inference.models import (
    RegulatorEvidenceImportReport,
    RegulatorInferenceReport,
    RegulatorSiteSignalImportReport,
)


def render_regulator_inference_summary_tsv(report: RegulatorInferenceReport) -> str:
    """Render the stable summary over one regulator inference report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "regulator_count",
            "entry_count",
            "site_regulation_entry_count",
            "protein_abundance_entry_count",
            "pathway_activity_entry_count",
            "unresolved_target_count",
            "high_scoring_entry_count",
            "note",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.regulator_count,
            report.summary.entry_count,
            report.summary.site_regulation_entry_count,
            report.summary.protein_abundance_entry_count,
            report.summary.pathway_activity_entry_count,
            report.summary.unresolved_target_count,
            report.summary.high_scoring_entry_count,
            report.note,
        )
    )
    return buffer.getvalue()


def render_regulator_inference_tsv(report: RegulatorInferenceReport) -> str:
    """Render one stable regulator inference table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "regulator",
            "evidence_type",
            "signal_surface",
            "source_name",
            "source_accession",
            "target_count",
            "matched_target_count",
            "coverage_fraction",
            "supporting_protein_refs",
            "supporting_site_keys",
            "supporting_pathway_ids",
            "direction",
            "score",
            "mean_log2_fold_change",
            "mean_activity_score_delta",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.regulator,
                entry.evidence_type.value,
                entry.signal_surface.value,
                entry.source_name or "",
                entry.source_accession or "",
                entry.target_count,
                entry.matched_target_count,
                _format_float(entry.coverage_fraction),
                ";".join(entry.supporting_protein_refs),
                ";".join(entry.supporting_site_keys),
                ";".join(entry.supporting_pathway_ids),
                entry.direction.value,
                _format_float(entry.score),
                _format_optional_float(entry.mean_log2_fold_change),
                _format_optional_float(entry.mean_activity_score_delta),
                entry.note,
            )
        )
    return buffer.getvalue()


def render_unresolved_regulator_target_tsv(report: RegulatorInferenceReport) -> str:
    """Render explicit unresolved regulator targets and why they failed."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "regulator",
            "evidence_type",
            "target_field",
            "target_value",
            "source_name",
            "source_accession",
            "reason",
        )
    )
    for entry in report.unresolved_targets:
        writer.writerow(
            (
                entry.regulator,
                entry.evidence_type.value,
                entry.target_field.value,
                entry.target_value,
                entry.source_name or "",
                entry.source_accession or "",
                entry.reason,
            )
        )
    return buffer.getvalue()


def render_rejected_regulator_evidence_tsv(
    report: RegulatorEvidenceImportReport,
) -> str:
    """Render rejected regulator evidence rows with stable reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "reason", "values"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, row.reason, _format_values(row.values)))
    return buffer.getvalue()


def render_rejected_regulator_site_signal_tsv(
    report: RegulatorSiteSignalImportReport,
) -> str:
    """Render rejected regulator site signal rows with stable reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("row_number", "reason", "values"))
    for row in report.rejected_rows:
        writer.writerow((row.row_number, row.reason, _format_values(row.values)))
    return buffer.getvalue()


def _format_float(value: float) -> str:
    return f"{value:.4g}"


def _format_optional_float(value: float | None) -> str:
    return "" if value is None else f"{value:.4g}"


def _format_values(values: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in sorted(values.items()))


__all__ = [
    "render_rejected_regulator_evidence_tsv",
    "render_rejected_regulator_site_signal_tsv",
    "render_regulator_inference_summary_tsv",
    "render_regulator_inference_tsv",
    "render_unresolved_regulator_target_tsv",
]
