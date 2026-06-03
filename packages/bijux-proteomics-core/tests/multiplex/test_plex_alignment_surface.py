# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_plex_integration_report,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_plex_integration_preserves_design_backed_sample_alignment() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_plex_integration_report(feature_bundle)

    assert len(report.sample_alignment) == 8
    sample_entry = next(
        entry for entry in report.sample_alignment if entry.sample_id == "plex_a_126"
    )
    assert sample_entry.analysis_included is True
    assert sample_entry.batch == "maxquant-a"
    assert sample_entry.bridge_sample_id == "plex_a_128N"
    assert sample_entry.bridge_channel == "128N"

    reference_entry = next(
        entry for entry in report.sample_alignment if entry.sample_id == "plex_a_128N"
    )
    assert reference_entry.analysis_included is False
    assert reference_entry.channel_role.value == "reference"
