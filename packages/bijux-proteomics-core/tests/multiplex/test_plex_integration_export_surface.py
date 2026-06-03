# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_plex_integration_report,
    build_tmt_reporter_feature_bundle,
    export_tmt_integrated_protein_matrix_tsv,
    export_tmt_plex_alignment_tsv,
    export_tmt_plex_effect_tsv,
    export_tmt_plex_integration_summary_tsv,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_plex_integration_exports_summary_alignment_effects_and_matrix(
    tmp_path: Path,
) -> None:
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

    summary_path = tmp_path / "tmt.integration.summary.tsv"
    alignment_path = tmp_path / "tmt.integration.alignment.tsv"
    effect_path = tmp_path / "tmt.integration.effects.tsv"
    matrix_path = tmp_path / "tmt.integration.proteins.tsv"

    export_tmt_plex_integration_summary_tsv(report, summary_path)
    export_tmt_plex_alignment_tsv(report, alignment_path)
    export_tmt_plex_effect_tsv(report, effect_path)
    export_tmt_integrated_protein_matrix_tsv(report, matrix_path)

    assert "integrated_sample_count" in summary_path.read_text(encoding="utf-8")
    assert "bridge_sample_id" in alignment_path.read_text(encoding="utf-8")
    assert "plex_a_128N" in alignment_path.read_text(encoding="utf-8")
    assert "ratio_to_global_bridge_median" in effect_path.read_text(encoding="utf-8")
    assert "P001" in matrix_path.read_text(encoding="utf-8")
    assert "plex_a_126\tplex_a_127N\tplex_b_126\tplex_b_127N" in matrix_path.read_text(
        encoding="utf-8"
    )
