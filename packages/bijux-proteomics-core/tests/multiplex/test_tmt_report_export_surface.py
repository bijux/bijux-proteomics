# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    export_tmt_channel_mapping_tsv,
    export_tmt_channel_totals_tsv,
    export_tmt_peptide_matrix_tsv,
    export_tmt_protein_matrix_tsv,
    export_tmt_report_summary_tsv,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_report_exports_write_summary_mapping_totals_and_matrices(
    tmp_path: Path,
) -> None:
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

    summary_path = tmp_path / "tmt.summary.tsv"
    mapping_path = tmp_path / "tmt.channel_mapping.tsv"
    totals_path = tmp_path / "tmt.channel_totals.tsv"
    peptide_path = tmp_path / "tmt.peptide_matrix.tsv"
    protein_path = tmp_path / "tmt.protein_matrix.tsv"

    export_tmt_report_summary_tsv(report, summary_path)
    export_tmt_channel_mapping_tsv(report, mapping_path)
    export_tmt_channel_totals_tsv(report, totals_path)
    export_tmt_peptide_matrix_tsv(report, peptide_path)
    export_tmt_protein_matrix_tsv(report, protein_path)

    assert "missing_channel_count" in summary_path.read_text()
    assert "plex-a\t129N\tplex_a_129N" in mapping_path.read_text()
    assert "total_intensity" in totals_path.read_text()
    assert "plex_a_129N" in peptide_path.read_text()
    assert "P001" in protein_path.read_text()
