# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtPlexIntegrationPolicy,
    TmtSearchResultSourceKind,
    build_tmt_plex_integration_report,
    build_tmt_reporter_feature_bundle,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_plex_integration_reports_bridge_median_shift_as_plex_effect() -> None:
    import_report = parse_tmt_reporter_table(
        _fixture("maxquant_tmt_evidence.tsv"),
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )
    design_report = parse_experimental_design_table(_fixture("tmt.design.tsv"))
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=tuple(design_report.accepted_entries),
    )

    report = build_tmt_plex_integration_report(
        feature_bundle,
        policy=TmtPlexIntegrationPolicy(plex_effect_ratio_threshold=1.01),
    )

    assert len(report.plex_effects) == 2
    assert report.summary.flagged_plex_effect_count == 2
    first = next(
        entry for entry in report.plex_effects if entry.multiplex_group == "plex-a"
    )
    assert first.bridge_sample_id == "plex_a_128N"
    assert round(first.bridge_total_intensity, 6) == 10100.0
    assert first.effect_ratio > 1.01
    assert first.flagged is True
