# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    build_tmt_ratio_report,
    build_tmt_reporter_feature_bundle,
    export_tmt_peptide_ratio_tsv,
    export_tmt_protein_ratio_tsv,
    export_tmt_ratio_summary_tsv,
    parse_tmt_reporter_table,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_tmt_ratio_exports_preserve_summary_and_missing_channel_ledgers(
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
    report = build_tmt_ratio_report(feature_bundle, control_channel="126")

    summary_path = tmp_path / "tmt.ratio.summary.tsv"
    peptide_path = tmp_path / "tmt.ratio.peptides.tsv"
    protein_path = tmp_path / "tmt.ratio.proteins.tsv"

    export_tmt_ratio_summary_tsv(report, summary_path)
    export_tmt_peptide_ratio_tsv(report, peptide_path)
    export_tmt_protein_ratio_tsv(report, protein_path)

    summary_lines = summary_path.read_text(encoding="utf-8").splitlines()
    assert summary_lines[0].startswith(
        "source_kind\tnormalization_method\tcontrol_channel"
    )
    assert "missing_ratio_count" in summary_lines[0]
    assert summary_lines[1].endswith("\t8")

    peptide_text = peptide_path.read_text(encoding="utf-8")
    assert "peptide_id\tpeptide_sequence\tprotein_refs" in peptide_text
    assert "sample_channel_missing" in peptide_text
    assert "PEPTIDE" in peptide_text

    protein_text = protein_path.read_text(encoding="utf-8")
    assert "protein_id\ttarget_kind\tprotein_refs" in protein_text
    assert "P001" in protein_text
    assert "\tprotein\t" in protein_text
