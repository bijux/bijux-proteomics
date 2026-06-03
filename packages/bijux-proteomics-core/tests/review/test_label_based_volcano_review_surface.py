# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.review import (
    VolcanoReviewPolicy,
    build_label_based_volcano_review,
)
from bijux_proteomics.workflow import build_silac_differential_analysis_report


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_build_label_based_volcano_review_preserves_raw_p_values_and_labels() -> None:
    design_report = parse_experimental_design_table(
        _fixture("silac_differential.design.tsv")
    )
    report = build_silac_differential_analysis_report(
        _fixture("silac_differential_features.tsv"),
        tuple(design_report.accepted_entries),
    )

    assert report.volcano_plot is not None
    review = build_label_based_volcano_review(
        report.volcano_plot,
        policy=VolcanoReviewPolicy(top_label_count=1),
    )

    assert review.source_kind.value == "label_based"
    assert review.labeled_point_count == 1
    assert any(point.raw_p_value > 0.0 for point in review.points)
    assert sum(1 for point in review.points if point.top_labeled) == 1
