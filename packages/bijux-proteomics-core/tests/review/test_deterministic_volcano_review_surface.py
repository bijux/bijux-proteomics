# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    VolcanoReviewPoint,
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    VolcanoReviewSourceKind,
    apply_volcano_review_policy,
    render_volcano_review_json,
    render_volcano_review_svg,
    render_volcano_review_tsv,
)


def _report() -> VolcanoReviewReport:
    points = apply_volcano_review_policy(
        (
            VolcanoReviewPoint(
                entity_id="P001",
                label="TP53",
                secondary_label="P001",
                log2_fold_change=2.0,
                raw_p_value=0.002,
                adjusted_p_value=0.01,
                negative_log10_adjusted_p_value=2.0,
                highlighted=True,
            ),
            VolcanoReviewPoint(
                entity_id="P002",
                label="MAPK1",
                secondary_label="P002",
                log2_fold_change=-1.5,
                raw_p_value=0.03,
                adjusted_p_value=0.08,
                negative_log10_adjusted_p_value=1.09691,
                highlighted=True,
            ),
            VolcanoReviewPoint(
                entity_id="P003",
                label="CALM1",
                secondary_label="P003",
                log2_fold_change=0.2,
                raw_p_value=0.4,
                adjusted_p_value=0.7,
                negative_log10_adjusted_p_value=0.154902,
                highlighted=False,
            ),
        ),
        policy=VolcanoReviewPolicy(top_label_count=2),
    )
    return VolcanoReviewReport(
        source_kind=VolcanoReviewSourceKind.LABEL_BASED,
        condition_a="control",
        condition_b="treated",
        x_axis_label="log2 fold change",
        y_axis_label="-log10 adjusted p-value",
        significant_point_count=2,
        labeled_point_count=2,
        policy=VolcanoReviewPolicy(top_label_count=2),
        points=points,
        note="generic volcano review preserves thresholds, labels, and significance",
    )


def test_volcano_review_renderers_are_deterministic_under_equivalent_point_order() -> (
    None
):
    report = _report()
    reordered = report.model_copy(update={"points": tuple(reversed(report.points))})

    assert render_volcano_review_json(report) == render_volcano_review_json(reordered)
    assert render_volcano_review_svg(report) == render_volcano_review_svg(reordered)
    assert render_volcano_review_tsv(report) == render_volcano_review_tsv(reordered)
