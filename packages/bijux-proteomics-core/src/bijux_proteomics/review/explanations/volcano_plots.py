# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared volcano-plot review surfaces and static renderers."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.ptm.differential_analysis import PtmDifferentialVolcanoPlot
    from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
    from bijux_proteomics.workflow.pipelines.dia_differential_analysis import (
        DiaDifferentialVolcanoPlot,
    )
    from bijux_proteomics.workflow.pipelines.label_based_differential_analysis import (
        LabelBasedDifferentialVolcanoPlot,
    )


class VolcanoReviewSourceKind(StrEnum):
    """Stable source kinds for volcano review payloads."""

    DIA = "dia"
    LABEL_BASED = "label_based"
    PTM = "ptm"
    QUANTIFICATION = "quantification"


class VolcanoReviewPolicy(JsonModel):
    """Threshold and label policy for volcano review surfaces."""

    model_config = ConfigDict(extra="forbid")

    adjusted_p_value_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    absolute_log2_fold_change_threshold: float = Field(default=1.0, ge=0.0)
    top_label_count: int = Field(default=10, ge=0)


class VolcanoReviewPoint(JsonModel):
    """One generic volcano review point."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    secondary_label: str | None = None
    log2_fold_change: float
    raw_p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float = Field(..., ge=0.0, le=1.0)
    negative_log10_adjusted_p_value: float = Field(..., ge=0.0)
    highlighted: bool
    top_labeled: bool = False


class VolcanoReviewReport(JsonModel):
    """Shared plot-ready volcano review payload."""

    model_config = ConfigDict(extra="forbid")

    source_kind: VolcanoReviewSourceKind
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    x_axis_label: str = Field(..., min_length=1)
    y_axis_label: str = Field(..., min_length=1)
    significant_point_count: int = Field(..., ge=0)
    labeled_point_count: int = Field(..., ge=0)
    policy: VolcanoReviewPolicy
    points: tuple[VolcanoReviewPoint, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def apply_volcano_review_policy(
    points: tuple[VolcanoReviewPoint, ...],
    *,
    policy: VolcanoReviewPolicy | None = None,
) -> tuple[VolcanoReviewPoint, ...]:
    """Apply top-label selection over generic volcano points."""

    active_policy = policy or VolcanoReviewPolicy()
    if active_policy.top_label_count == 0:
        return points
    ranked = sorted(
        points,
        key=lambda point: (
            not point.highlighted,
            -point.negative_log10_adjusted_p_value,
            -abs(point.log2_fold_change),
            point.label,
            point.entity_id,
        ),
    )
    top_ids = {
        id(point)
        for point in ranked[: active_policy.top_label_count]
    }
    return tuple(
        point.model_copy(update={"top_labeled": id(point) in top_ids}) for point in points
    )


def render_volcano_review_json(report: VolcanoReviewReport) -> str:
    """Render one volcano review payload as deterministic JSON."""

    stable_report = report.model_copy(
        update={"points": tuple(sorted(report.points, key=lambda point: point.entity_id))}
    )
    return stable_report.to_stable_json() + "\n"


def render_volcano_review_svg(report: VolcanoReviewReport) -> str:
    """Render one volcano review payload as static SVG."""

    width = 960.0
    height = 640.0
    left_margin = 84.0
    right_margin = 32.0
    top_margin = 32.0
    bottom_margin = 72.0
    usable_width = width - left_margin - right_margin
    usable_height = height - top_margin - bottom_margin

    stable_points = tuple(sorted(report.points, key=lambda point: point.entity_id))
    if stable_points:
        min_x = min(point.log2_fold_change for point in stable_points)
        max_x = max(point.log2_fold_change for point in stable_points)
        max_y = max(point.negative_log10_adjusted_p_value for point in stable_points)
    else:
        min_x = -1.0
        max_x = 1.0
        max_y = 1.0
    if min_x == max_x:
        min_x -= 1.0
        max_x += 1.0
    if max_y <= 0.0:
        max_y = 1.0
    x_padding = max((max_x - min_x) * 0.08, 0.5)
    min_x -= x_padding
    max_x += x_padding
    max_y *= 1.12
    threshold_y = _negative_log10(report.policy.adjusted_p_value_threshold)

    def project_x(value: float) -> float:
        return left_margin + (value - min_x) / (max_x - min_x) * usable_width

    def project_y(value: float) -> float:
        return top_margin + usable_height - (value / max_y) * usable_height

    rows = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{int(width)}' height='{int(height)}' viewBox='0 0 {int(width)} {int(height)}'>",
        f"<rect x='0' y='0' width='{int(width)}' height='{int(height)}' fill='white' />",
        f"<text x='{int(left_margin)}' y='20' font-size='18' font-family='monospace'>Volcano plot: {escape(report.condition_a)} vs {escape(report.condition_b)}</text>",
        f"<line x1='{left_margin:.2f}' y1='{top_margin + usable_height:.2f}' x2='{left_margin + usable_width:.2f}' y2='{top_margin + usable_height:.2f}' stroke='#222' stroke-width='1.5' />",
        f"<line x1='{left_margin:.2f}' y1='{top_margin:.2f}' x2='{left_margin:.2f}' y2='{top_margin + usable_height:.2f}' stroke='#222' stroke-width='1.5' />",
    ]
    for x_value in (
        -report.policy.absolute_log2_fold_change_threshold,
        0.0,
        report.policy.absolute_log2_fold_change_threshold,
    ):
        rows.append(
            f"<line x1='{project_x(x_value):.2f}' y1='{top_margin:.2f}' x2='{project_x(x_value):.2f}' y2='{top_margin + usable_height:.2f}' stroke='#c7c7c7' stroke-dasharray='4 4' />"
        )
    rows.append(
        f"<line x1='{left_margin:.2f}' y1='{project_y(threshold_y):.2f}' x2='{left_margin + usable_width:.2f}' y2='{project_y(threshold_y):.2f}' stroke='#c7c7c7' stroke-dasharray='4 4' />"
    )
    for point in stable_points:
        cx = project_x(point.log2_fold_change)
        cy = project_y(point.negative_log10_adjusted_p_value)
        fill = "#cc3311" if point.highlighted else "#6b7280"
        radius = 4.5 if point.top_labeled else 3.5
        rows.append(
            f"<circle cx='{cx:.2f}' cy='{cy:.2f}' r='{radius:.2f}' fill='{fill}' fill-opacity='0.85' />"
        )
        if point.top_labeled:
            label = escape(point.label)
            rows.append(
                f"<text x='{cx + 6:.2f}' y='{cy - 6:.2f}' font-size='11' font-family='monospace' fill='#111'>{label}</text>"
            )
    rows.extend(
        [
            f"<text x='{left_margin + usable_width / 2:.2f}' y='{height - 24:.2f}' font-size='14' text-anchor='middle' font-family='monospace'>{escape(report.x_axis_label)}</text>",
            f"<text transform='translate(18 {top_margin + usable_height / 2:.2f}) rotate(-90)' font-size='14' text-anchor='middle' font-family='monospace'>{escape(report.y_axis_label)}</text>",
            f"<text x='{left_margin:.2f}' y='{height - 8:.2f}' font-size='11' font-family='monospace'>thresholds: |log2fc| &gt;= {report.policy.absolute_log2_fold_change_threshold:g}, fdr &lt;= {report.policy.adjusted_p_value_threshold:g}</text>",
            "</svg>\n",
        ]
    )
    return "".join(rows)


def render_volcano_review_html(report: VolcanoReviewReport) -> str:
    """Render one volcano review payload as static HTML with embedded SVG."""

    svg = render_volcano_review_svg(report)
    return (
        "<html><head><title>Bijux Proteomics Volcano Plot</title></head><body>"
        f"<h1>Volcano plot: {escape(report.condition_a)} vs {escape(report.condition_b)}</h1>"
        f"<p><strong>Source</strong>: {escape(report.source_kind.value)} | "
        f"<strong>Significant points</strong>: {report.significant_point_count} | "
        f"<strong>Labeled points</strong>: {report.labeled_point_count}</p>"
        f"{svg}"
        "</body></html>\n"
    )


def export_volcano_review_json(report: VolcanoReviewReport, path: Path) -> None:
    """Write one volcano review payload as JSON."""

    path.write_text(render_volcano_review_json(report), encoding="utf-8")


def export_volcano_review_svg(report: VolcanoReviewReport, path: Path) -> None:
    """Write one volcano review payload as SVG."""

    path.write_text(render_volcano_review_svg(report), encoding="utf-8")


def export_volcano_review_html(report: VolcanoReviewReport, path: Path) -> None:
    """Write one volcano review payload as HTML."""

    path.write_text(render_volcano_review_html(report), encoding="utf-8")


def render_volcano_review_tsv(report: VolcanoReviewReport) -> str:
    """Render one generic volcano review payload as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "label",
            "secondary_label",
            "log2_fold_change",
            "raw_p_value",
            "adjusted_p_value",
            "negative_log10_adjusted_p_value",
            "highlighted",
            "top_labeled",
        )
    )
    for point in sorted(report.points, key=lambda point: point.entity_id):
        writer.writerow(
            (
                point.entity_id,
                point.label,
                point.secondary_label or "",
                f"{point.log2_fold_change:g}",
                f"{point.raw_p_value:g}",
                f"{point.adjusted_p_value:g}",
                f"{point.negative_log10_adjusted_p_value:g}",
                str(point.highlighted).lower(),
                str(point.top_labeled).lower(),
            )
        )
    return handle.getvalue()


def build_label_based_volcano_review(
    plot: LabelBasedDifferentialVolcanoPlot,
    *,
    policy: VolcanoReviewPolicy | None = None,
) -> VolcanoReviewReport:
    """Build a shared volcano review payload from a labeled differential volcano plot."""

    active_policy = policy or VolcanoReviewPolicy()
    points = tuple(
        VolcanoReviewPoint(
            entity_id=point.entity_id,
            label=point.protein_refs[0] if point.protein_refs else point.entity_id,
            secondary_label=(
                point.entity_id
                if point.protein_refs and point.protein_refs[0] != point.entity_id
                else None
            ),
            log2_fold_change=point.log2_fold_change,
            raw_p_value=point.raw_p_value,
            adjusted_p_value=point.adjusted_p_value,
            negative_log10_adjusted_p_value=point.negative_log10_adjusted_p_value,
            highlighted=point.highlighted,
        )
        for point in plot.points
    )
    labeled_points = apply_volcano_review_policy(points, policy=active_policy)
    return VolcanoReviewReport(
        source_kind=VolcanoReviewSourceKind.LABEL_BASED,
        condition_a=plot.condition_a,
        condition_b=plot.condition_b,
        x_axis_label="log2 fold change",
        y_axis_label="-log10 adjusted p-value",
        significant_point_count=plot.significant_point_count,
        labeled_point_count=sum(1 for point in labeled_points if point.top_labeled),
        policy=active_policy,
        points=labeled_points,
        note=(
            "shared volcano review preserves raw and adjusted significance over one labeled differential contrast"
        ),
    )


def build_dia_volcano_review(
    plot: DiaDifferentialVolcanoPlot,
    *,
    policy: VolcanoReviewPolicy | None = None,
) -> VolcanoReviewReport:
    """Build a shared volcano review payload from a DIA differential volcano plot."""

    active_policy = policy or VolcanoReviewPolicy()
    points = tuple(
        VolcanoReviewPoint(
            entity_id=point.entity_id,
            label=point.protein_refs[0] if point.protein_refs else point.entity_id,
            secondary_label=(
                point.entity_id
                if point.protein_refs and point.protein_refs[0] != point.entity_id
                else None
            ),
            log2_fold_change=point.log2_fold_change,
            raw_p_value=point.raw_p_value,
            adjusted_p_value=point.adjusted_p_value,
            negative_log10_adjusted_p_value=point.negative_log10_adjusted_p_value,
            highlighted=point.highlighted,
        )
        for point in plot.points
    )
    labeled_points = apply_volcano_review_policy(points, policy=active_policy)
    return VolcanoReviewReport(
        source_kind=VolcanoReviewSourceKind.DIA,
        condition_a=plot.condition_a,
        condition_b=plot.condition_b,
        x_axis_label="log2 fold change",
        y_axis_label="-log10 adjusted p-value",
        significant_point_count=plot.significant_point_count,
        labeled_point_count=sum(1 for point in labeled_points if point.top_labeled),
        policy=active_policy,
        points=labeled_points,
        note=(
            "shared volcano review preserves raw and adjusted significance over one DIA differential contrast"
        ),
    )


def build_ptm_volcano_review(
    plot: PtmDifferentialVolcanoPlot,
    *,
    policy: VolcanoReviewPolicy | None = None,
) -> VolcanoReviewReport:
    """Build a shared volcano review payload from a PTM differential volcano plot."""

    active_policy = policy or VolcanoReviewPolicy()
    points = tuple(
        VolcanoReviewPoint(
            entity_id=point.site_key,
            label=f"{point.protein_ref}:{point.residue}{point.position}",
            secondary_label=point.modification_name,
            log2_fold_change=point.plotted_log2_fold_change,
            raw_p_value=point.raw_p_value,
            adjusted_p_value=point.adjusted_p_value,
            negative_log10_adjusted_p_value=point.negative_log10_adjusted_p_value,
            highlighted=point.highlighted,
        )
        for point in plot.points
    )
    labeled_points = apply_volcano_review_policy(points, policy=active_policy)
    return VolcanoReviewReport(
        source_kind=VolcanoReviewSourceKind.PTM,
        condition_a=plot.condition_a,
        condition_b=plot.condition_b,
        x_axis_label="log2 fold change",
        y_axis_label="-log10 adjusted p-value",
        significant_point_count=plot.significant_point_count,
        labeled_point_count=sum(1 for point in labeled_points if point.top_labeled),
        policy=active_policy,
        points=labeled_points,
        note=(
            "shared volcano review preserves raw and adjusted significance over one PTM site differential contrast"
        ),
    )


def build_quantification_volcano_review(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    policy: VolcanoReviewPolicy | None = None,
) -> VolcanoReviewReport:
    """Build a shared volcano review payload from a quantification differential report."""

    active_policy = policy or VolcanoReviewPolicy()
    protein_ref_lookup = protein_refs_by_entity or {}
    points = tuple(
        VolcanoReviewPoint(
            entity_id=entry.entity_id,
            label=(
                protein_ref_lookup[entry.entity_id][0]
                if protein_ref_lookup.get(entry.entity_id)
                else entry.entity_id
            ),
            secondary_label=(
                entry.entity_id
                if protein_ref_lookup.get(entry.entity_id)
                and protein_ref_lookup[entry.entity_id][0] != entry.entity_id
                else None
            ),
            log2_fold_change=entry.log2_fold_change,
            raw_p_value=entry.p_value,
            adjusted_p_value=(
                1.0 if entry.adjusted_p_value is None else entry.adjusted_p_value
            ),
            negative_log10_adjusted_p_value=_negative_log10(
                1.0 if entry.adjusted_p_value is None else entry.adjusted_p_value
            ),
            highlighted=(
                entry.adjusted_p_value is not None
                and entry.adjusted_p_value <= active_policy.adjusted_p_value_threshold
                and abs(entry.log2_fold_change)
                >= active_policy.absolute_log2_fold_change_threshold
            ),
        )
        for entry in report.entries
    )
    labeled_points = apply_volcano_review_policy(points, policy=active_policy)
    return VolcanoReviewReport(
        source_kind=VolcanoReviewSourceKind.QUANTIFICATION,
        condition_a=report.condition_a,
        condition_b=report.condition_b,
        x_axis_label="log2 fold change",
        y_axis_label="-log10 adjusted p-value",
        significant_point_count=sum(1 for point in labeled_points if point.highlighted),
        labeled_point_count=sum(1 for point in labeled_points if point.top_labeled),
        policy=active_policy,
        points=labeled_points,
        note=(
            "shared volcano review preserves raw and adjusted significance over one quantification differential contrast"
        ),
    )


def _negative_log10(value: float) -> float:
    bounded = max(value, 1e-300)
    return -math.log10(bounded)
