# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math
from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_ratio_report,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_ratio_report_builds_peptide_sample_control_ratios() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_ratio_report(feature_bundle, control_channel="126")

    assert report.summary.source_kind.value == "raw"
    assert report.summary.control_channel == "126"
    assert report.summary.multiplex_group_count == 2
    assert report.summary.peptide_ratio_count == 12
    assert report.summary.protein_ratio_count == 12
    assert report.summary.missing_ratio_count == 8
    first = next(
        entry
        for entry in report.peptide_ratios
        if entry.multiplex_group == "plex-a"
        and entry.peptide_id == "PEPTIDE"
        and entry.numerator_channel == "127N"
    )
    assert first.control_sample_id == "plex_a_126"
    assert first.ratio is not None
    assert first.log2_ratio is not None
    assert round(first.ratio, 6) == round(1400.0 / 1200.0, 6)
    assert round(first.log2_ratio, 6) == round(math.log2(1400.0 / 1200.0), 6)
    missing = next(
        entry
        for entry in report.peptide_ratios
        if entry.multiplex_group == "plex-a"
        and entry.peptide_id == "PEPTIDE"
        and entry.numerator_channel == "129N"
    )
    assert missing.ratio is None
    assert missing.missing_reason == "sample_channel_missing"
    protein = next(
        entry
        for entry in report.protein_ratios
        if entry.multiplex_group == "plex-a"
        and entry.protein_id == "P001"
        and entry.numerator_channel == "127N"
    )
    assert protein.target_kind.value == "protein"
    assert protein.ratio is not None
    assert round(protein.ratio, 6) == round(1400.0 / 1200.0, 6)
