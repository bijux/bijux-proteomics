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


def test_tmt_plex_integration_report_builds_bridge_normalized_protein_matrix() -> None:
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

    assert report.summary.multiplex_group_count == 2
    assert report.summary.bridge_group_count == 2
    assert report.summary.integrated_sample_count == 4
    assert report.summary.protein_row_count == 2
    assert report.integrated_protein_matrix.sample_ids == (
        "plex_a_126",
        "plex_a_127N",
        "plex_b_126",
        "plex_b_127N",
    )
    row = next(
        row for row in report.integrated_protein_matrix.rows if row.entity_id == "P001"
    )
    values = {value.sample_id: value.abundance for value in row.values}
    assert round(values["plex_a_126"] or 0.0, 6) == round(1200.0 / 6000.0, 6)
    assert round(values["plex_b_127N"] or 0.0, 6) == round(1700.0 / 6500.0, 6)
