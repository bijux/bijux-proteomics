# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned batch-effect estimation surfaces for quantitative proteomics."""

from __future__ import annotations

import csv
from io import StringIO
import math
from pathlib import Path

import numpy as np

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    BatchAssociatedPrincipalComponentEntry,
    BatchEffectAdvisoryReport,
    BatchEffectBatchEntry,
    LabelFreeQuantTable,
    QuantAssessmentDisposition,
    _log2_values,
)
from bijux_proteomics.quantification.matrix.design_matrix import _resolve_design_value
from bijux_proteomics.quantification.provenance.sample_exploration import (
    build_sample_pca_report,
    build_sample_pca_variance_report,
)
from bijux_proteomics.study.design_diagnostics import (
    detect_batch_condition_confounding,
)


def build_batch_effect_estimator_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str = "batch",
    shift_threshold: float = 0.5,
    component_association_threshold: float = 0.35,
) -> BatchEffectAdvisoryReport:
    """Estimate batch structure from abundance shifts and batch-associated PCs."""
    batch_by_sample = _batch_by_sample_id(
        design_entries,
        batch_field=batch_field,
    )
    if not batch_by_sample:
        return BatchEffectAdvisoryReport(
            disposition=QuantAssessmentDisposition.ADVISORY,
            batch_field=batch_field,
            global_median_log2_abundance=0.0,
            batches=(),
            batch_variance_proxy=0.0,
            principal_components=(),
            batch_associated_component_count=0,
            fully_confounded_with_condition=False,
            batch_correction_blocked=False,
            batch_warning=None,
            note="No batch metadata was provided; batch estimation remains empty.",
        )

    per_sample = {
        sample_id: _log2_values(table, sample_id) for sample_id in table.sample_ids
    }
    finite_samples = [values for values in per_sample.values() if values.size > 0]
    global_median = (
        float(np.median(np.concatenate(finite_samples))) if finite_samples else 0.0
    )
    grouped_batches: dict[str, list[str]] = {}
    for sample_id, batch_id in sorted(batch_by_sample.items()):
        if sample_id in table.sample_ids:
            grouped_batches.setdefault(batch_id, []).append(sample_id)

    batches: list[BatchEffectBatchEntry] = []
    for batch_id, sample_ids in sorted(grouped_batches.items()):
        values = [
            per_sample[sample_id]
            for sample_id in sample_ids
            if per_sample[sample_id].size > 0
        ]
        batch_median = float(np.median(np.concatenate(values))) if values else 0.0
        shift = batch_median - global_median
        batches.append(
            BatchEffectBatchEntry(
                batch_id=batch_id,
                sample_ids=tuple(sorted(sample_ids)),
                median_log2_abundance=batch_median,
                shift_from_global=shift,
                flagged=abs(shift) >= shift_threshold,
            )
        )

    pca_report = build_sample_pca_report(table, design_entries)
    variance_report = build_sample_pca_variance_report(table, design_entries)
    explained_variance = {
        entry.component_index: entry.explained_variance_ratio
        for entry in variance_report.entries
    }
    pc_vectors = {
        1: tuple(entry.pc1 for entry in pca_report.entries),
        2: tuple(entry.pc2 for entry in pca_report.entries),
    }
    principal_components: list[BatchAssociatedPrincipalComponentEntry] = []
    for component_index, scores in pc_vectors.items():
        if component_index not in explained_variance:
            continue
        association = _batch_association_ratio(
            scores=scores,
            sample_ids=tuple(entry.sample_id for entry in pca_report.entries),
            batch_by_sample=batch_by_sample,
        )
        principal_components.append(
            BatchAssociatedPrincipalComponentEntry(
                component_index=component_index,
                component_label=f"PC{component_index}",
                explained_variance_ratio=explained_variance[component_index],
                batch_association_ratio=association,
                associated_with_batch=association >= component_association_threshold,
            )
        )

    batch_variance_proxy = min(
        1.0,
        sum(
            entry.explained_variance_ratio * entry.batch_association_ratio
            for entry in principal_components
            if entry.associated_with_batch
        ),
    )
    relevant_design_entries = tuple(
        entry for entry in design_entries if entry.sample_id in table.sample_ids
    )
    fully_confounded = detect_batch_condition_confounding(
        relevant_design_entries,
        batch_field=batch_field,
    ).is_confounded
    correction_blocked = fully_confounded
    warning = _batch_warning(
        batches=tuple(batches),
        principal_components=tuple(principal_components),
        fully_confounded_with_condition=fully_confounded,
    )
    return BatchEffectAdvisoryReport(
        disposition=(
            QuantAssessmentDisposition.ENFORCED
            if correction_blocked
            else QuantAssessmentDisposition.ADVISORY
        ),
        batch_field=batch_field,
        global_median_log2_abundance=global_median,
        batches=tuple(batches),
        batch_variance_proxy=batch_variance_proxy,
        principal_components=tuple(principal_components),
        batch_associated_component_count=sum(
            1 for entry in principal_components if entry.associated_with_batch
        ),
        fully_confounded_with_condition=fully_confounded,
        batch_correction_blocked=correction_blocked,
        batch_warning=warning,
        note=_batch_note(
            fully_confounded_with_condition=fully_confounded,
            batch_variance_proxy=batch_variance_proxy,
            flagged_batch_count=sum(1 for entry in batches if entry.flagged),
        ),
    )


def render_batch_effect_summary_tsv(report: BatchEffectAdvisoryReport) -> str:
    """Render a stable one-row batch-effect summary table."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "batch_field",
            "disposition",
            "global_median_log2_abundance",
            "batch_count",
            "flagged_batch_count",
            "batch_variance_proxy",
            "batch_associated_component_count",
            "fully_confounded_with_condition",
            "batch_correction_blocked",
            "batch_warning",
            "note",
        ]
    )
    writer.writerow(
        [
            report.batch_field,
            report.disposition.value,
            report.global_median_log2_abundance,
            len(report.batches),
            sum(1 for entry in report.batches if entry.flagged),
            report.batch_variance_proxy,
            report.batch_associated_component_count,
            report.fully_confounded_with_condition,
            report.batch_correction_blocked,
            report.batch_warning or "",
            report.note,
        ]
    )
    return buffer.getvalue()


def render_batch_effect_batches_tsv(report: BatchEffectAdvisoryReport) -> str:
    """Render stable batch-level shift rows for one batch-effect report."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "batch_id",
            "sample_ids",
            "median_log2_abundance",
            "shift_from_global",
            "flagged",
        ]
    )
    for entry in sorted(report.batches, key=lambda item: item.batch_id):
        writer.writerow(
            [
                entry.batch_id,
                ";".join(entry.sample_ids),
                entry.median_log2_abundance,
                entry.shift_from_global,
                entry.flagged,
            ]
        )
    return buffer.getvalue()


def render_batch_effect_principal_components_tsv(
    report: BatchEffectAdvisoryReport,
) -> str:
    """Render stable principal-component batch-association rows."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "component_index",
            "component_label",
            "explained_variance_ratio",
            "batch_association_ratio",
            "associated_with_batch",
        ]
    )
    for entry in sorted(
        report.principal_components,
        key=lambda item: item.component_index,
    ):
        writer.writerow(
            [
                entry.component_index,
                entry.component_label,
                entry.explained_variance_ratio,
                entry.batch_association_ratio,
                entry.associated_with_batch,
            ]
        )
    return buffer.getvalue()


def export_batch_effect_summary_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write a stable batch-effect summary table."""
    path.write_text(render_batch_effect_summary_tsv(report), encoding="utf-8")


def export_batch_effect_batches_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write stable batch-level shift rows."""
    path.write_text(render_batch_effect_batches_tsv(report), encoding="utf-8")


def export_batch_effect_principal_components_tsv(
    report: BatchEffectAdvisoryReport,
    path: Path,
) -> None:
    """Write stable principal-component batch-association rows."""
    path.write_text(
        render_batch_effect_principal_components_tsv(report),
        encoding="utf-8",
    )


def _batch_by_sample_id(
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    batch_field: str,
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in design_entries:
        value = _resolve_design_value(entry, batch_field)
        if batch_field == "batch" and value in (None, ""):
            value = entry.instrument
        if value not in (None, ""):
            mapping[entry.sample_id] = str(value)
    return mapping


def _batch_association_ratio(
    *,
    scores: tuple[float, ...],
    sample_ids: tuple[str, ...],
    batch_by_sample: dict[str, str],
) -> float:
    included = [
        (score, batch_by_sample.get(sample_id))
        for score, sample_id in zip(scores, sample_ids, strict=False)
        if batch_by_sample.get(sample_id) not in (None, "")
    ]
    if len(included) < 2:
        return 0.0
    score_values = np.array([score for score, _batch in included], dtype=float)
    if score_values.size < 2:
        return 0.0
    grand_mean = float(np.mean(score_values))
    total_ss = float(np.sum((score_values - grand_mean) ** 2))
    if total_ss <= 0.0 or not math.isfinite(total_ss):
        return 0.0
    grouped: dict[str, list[float]] = {}
    for score, batch_id in included:
        grouped.setdefault(batch_id or "", []).append(score)
    between_ss = 0.0
    for values in grouped.values():
        if not values:
            continue
        batch_mean = float(np.mean(np.array(values, dtype=float)))
        between_ss += len(values) * (batch_mean - grand_mean) ** 2
    return max(0.0, min(1.0, between_ss / total_ss))


def _batch_warning(
    *,
    batches: tuple[BatchEffectBatchEntry, ...],
    principal_components: tuple[BatchAssociatedPrincipalComponentEntry, ...],
    fully_confounded_with_condition: bool,
) -> str | None:
    if fully_confounded_with_condition:
        return "batch is fully confounded with condition; batch correction is blocked"
    if any(entry.flagged for entry in batches) or any(
        entry.associated_with_batch for entry in principal_components
    ):
        return (
            "batch-associated structure was detected and should be reviewed before correction or interpretation"
        )
    return None


def _batch_note(
    *,
    fully_confounded_with_condition: bool,
    batch_variance_proxy: float,
    flagged_batch_count: int,
) -> str:
    if fully_confounded_with_condition:
        return (
            "batch estimation detected full confounding between batch and condition and therefore blocks batch correction"
        )
    if flagged_batch_count > 0 or batch_variance_proxy > 0.0:
        return (
            "batch estimation preserves global shifts and batch-associated principal components for quantitative review"
        )
    return "batch estimation did not detect shifts or principal-component structure beyond the current thresholds"
