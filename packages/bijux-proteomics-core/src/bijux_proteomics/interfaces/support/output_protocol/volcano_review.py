# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Volcano review policy and artifact export helpers for interface workflows."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    export_volcano_review_html,
    export_volcano_review_json,
    export_volcano_review_svg,
)


def _build_volcano_review_policy(
    *,
    adjusted_p_value_threshold: float,
    absolute_log2_fold_change_threshold: float,
    top_label_count: int,
) -> VolcanoReviewPolicy:
    return VolcanoReviewPolicy(
        adjusted_p_value_threshold=adjusted_p_value_threshold,
        absolute_log2_fold_change_threshold=absolute_log2_fold_change_threshold,
        top_label_count=top_label_count,
    )


def _export_volcano_review_assets(
    *,
    review_report: VolcanoReviewReport,
    json_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
) -> None:
    if json_out is not None:
        export_volcano_review_json(review_report, json_out)
    if svg_out is not None:
        export_volcano_review_svg(review_report, svg_out)
    if html_out is not None:
        export_volcano_review_html(review_report, html_out)
