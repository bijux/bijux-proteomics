# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_normalization_report,
    build_tmt_reporter_feature_bundle,
    export_tmt_channel_distribution_tsv,
    export_tmt_normalization_summary_tsv,
    export_tmt_normalization_transform_tsv,
    export_tmt_normalized_peptide_matrix_tsv,
    export_tmt_normalized_protein_matrix_tsv,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_normalization_exports_write_summary_distribution_and_matrices(
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
    report = build_tmt_normalization_report(feature_bundle)

    summary_path = tmp_path / "tmt.normalization.summary.tsv"
    transform_path = tmp_path / "tmt.normalization.transforms.tsv"
    distribution_path = tmp_path / "tmt.normalization.distributions.tsv"
    peptide_path = tmp_path / "tmt.normalization.peptides.tsv"
    protein_path = tmp_path / "tmt.normalization.proteins.tsv"

    export_tmt_normalization_summary_tsv(report, summary_path)
    export_tmt_normalization_transform_tsv(report, transform_path)
    export_tmt_channel_distribution_tsv(report, distribution_path)
    export_tmt_normalized_peptide_matrix_tsv(report, peptide_path)
    export_tmt_normalized_protein_matrix_tsv(report, protein_path)

    assert "before_flagged_channel_count" in summary_path.read_text(encoding="utf-8")
    assert "scale_factor" in transform_path.read_text(encoding="utf-8")
    assert "stage\tmultiplex_group\tmultiplex_channel" in distribution_path.read_text(
        encoding="utf-8"
    )
    assert "plex_a_129N" in peptide_path.read_text(encoding="utf-8")
    assert "entity_id\ttarget_kind\tprotein_refs" in protein_path.read_text(
        encoding="utf-8"
    )
