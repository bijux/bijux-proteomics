# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import build_biological_result_report_bundle


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_biological_result_report_bundle_preserves_differential_and_review_surfaces() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.sample_count == 6
    assert report.summary.heatmap_entity_count >= 3
    assert report.volcano_review.source_kind.value == "quantification"
    assert report.volcano_review.significant_point_count >= 3
    assert report.sample_exploration_report.summary.sample_count == 6
    assert report.heatmap_report.summary.output_entity_count >= 3
