# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtNormalizationMethod,
    TmtSearchResultSourceKind,
    build_tmt_normalization_report,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_median_normalization_report_preserves_before_after_review() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_normalization_report(feature_bundle)

    assert report.summary.method is TmtNormalizationMethod.MEDIAN
    assert report.summary.channel_count == 8
    assert report.summary.transform_count == 8
    assert report.summary.before_flagged_channel_count >= 1
    assert report.summary.after_flagged_channel_count < report.summary.before_flagged_channel_count
    assert report.before_report.summary.channel_total_count == 8
    assert report.after_report.summary.channel_total_count == 8
    assert len(report.channel_distributions) == 16
    assert all(entry.scale_factor is not None for entry in report.transforms)
