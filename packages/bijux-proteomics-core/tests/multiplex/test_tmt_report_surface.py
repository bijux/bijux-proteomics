# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_reporter_matrix_report_builds_channel_totals_and_matrices() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_entries = parse_experimental_design_table(
        _fixture("tmt.design.tsv")
    ).accepted_entries
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=design_entries,
    )

    report = build_tmt_reporter_matrix_report(feature_bundle)

    assert report.summary.feature_record_count == 16
    assert report.summary.missing_channel_count == 2
    assert report.summary.peptide_row_count == 2
    assert report.summary.protein_row_count == 2
    plex_a_sample = next(
        entry for entry in report.channel_totals if entry.sample_id == "plex_a_126"
    )
    assert plex_a_sample.total_intensity == 2000.0
    assert plex_a_sample.observed_row_count == 2
    plex_a_missing = next(
        entry for entry in report.channel_totals if entry.sample_id == "plex_a_129N"
    )
    assert plex_a_missing.total_intensity == 0.0
    assert plex_a_missing.observed_row_count == 0
    assert plex_a_missing.missing_row_count == 2
    assert report.peptide_matrix.sample_ids == (
        "plex_a_126",
        "plex_a_127N",
        "plex_a_128N",
        "plex_a_129N",
        "plex_b_126",
        "plex_b_127N",
        "plex_b_128N",
        "plex_b_129N",
    )
