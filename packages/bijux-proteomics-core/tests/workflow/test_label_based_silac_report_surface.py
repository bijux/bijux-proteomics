# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    LabelBasedDifferentialSourceKind,
    build_silac_label_based_report_bundle,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_silac_label_based_report_bundle_preserves_ratio_validation_and_differential_surfaces() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("silac_differential.design.tsv")
        ).accepted_entries
    )

    report = build_silac_label_based_report_bundle(
        _fixture("silac_differential_features.tsv"),
        design_entries,
    )

    assert report.source_kind is LabelBasedDifferentialSourceKind.SILAC
    assert report.silac_ratio_report is not None
    assert report.silac_ratio_report.summary.protein_ratio_count == 12
    assert report.silac_validation_report is not None
    assert report.silac_validation_report.summary.sample_count == 4
    assert report.differential_analysis_report.differential_abundance_report is not None
    assert report.summary.sample_count == 4
    assert report.summary.differential_result_count == 3
