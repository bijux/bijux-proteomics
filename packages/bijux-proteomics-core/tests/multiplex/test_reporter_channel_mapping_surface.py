# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_reporter_feature_bundle_maps_channels_and_preserves_missing_design_channels() -> (
    None
):
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_entries = parse_experimental_design_table(
        _fixture("tmt.design.tsv")
    ).accepted_entries

    bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=design_entries,
    )

    assert bundle.summary.accepted_source_row_count == 4
    assert bundle.summary.multiplex_group_count == 2
    assert bundle.summary.mapped_channel_count == 8
    assert bundle.summary.missing_channel_count == 2
    assert bundle.summary.feature_record_count == 16
    missing = next(
        entry
        for entry in bundle.channel_mapping
        if entry.multiplex_group == "plex-a" and entry.multiplex_channel == "129N"
    )
    assert missing.source_column_present is False
    assert missing.mapped_to_design is True
    placeholder = next(
        record
        for record in bundle.feature_records
        if record.sample_id == "plex_a_129N" and record.feature_id == "1:129N"
    )
    assert placeholder.intensity is None
    assert placeholder.missing_value_kind.value == "missing_not_observed"
