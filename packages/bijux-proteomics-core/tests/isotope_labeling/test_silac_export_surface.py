# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.isotope_labeling import (
    SilacLabel,
    SilacQuantificationPolicy,
    build_silac_ratio_report,
    export_silac_peptide_ratio_tsv,
    export_silac_protein_ratio_tsv,
    export_silac_ratio_summary_tsv,
    parse_silac_feature_table,
    render_silac_peptide_ratio_tsv,
    render_silac_protein_ratio_tsv,
    render_silac_ratio_summary_tsv,
)


def _fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent / "fixtures" / "isotope_labeling" / name
    )


def test_silac_ratio_renderers_emit_summary_and_ledgers(tmp_path: Path) -> None:
    import_report = parse_silac_feature_table(_fixture("silac_features.tsv"))
    report = build_silac_ratio_report(
        import_report,
        policy=SilacQuantificationPolicy(
            expected_labels=(
                SilacLabel.LIGHT,
                SilacLabel.MEDIUM,
                SilacLabel.HEAVY,
            ),
            separate_charge_states=False,
        ),
    )

    summary_tsv = render_silac_ratio_summary_tsv(report)
    peptide_tsv = render_silac_peptide_ratio_tsv(report)
    protein_tsv = render_silac_protein_ratio_tsv(report)

    assert (
        "sample_count\texpected_label_count\tpeptide_ratio_count\tprotein_ratio_count\tmissing_ratio_count"
        in summary_tsv
    )
    assert "\tPEPTIDE\tPEPTIDE\t" in peptide_tsv
    assert "numerator_label_missing" in peptide_tsv
    assert (
        "sample_a\tP001\tP001\tPEPTIDE\tmedium\tlight\t2000.0\t1500.0\t1.3333333333333333"
        in protein_tsv
    )

    summary_path = tmp_path / "silac.summary.tsv"
    peptide_path = tmp_path / "silac.peptides.tsv"
    protein_path = tmp_path / "silac.proteins.tsv"
    export_silac_ratio_summary_tsv(report, summary_path)
    export_silac_peptide_ratio_tsv(report, peptide_path)
    export_silac_protein_ratio_tsv(report, protein_path)

    assert summary_path.read_text(encoding="utf-8") == summary_tsv
    assert peptide_path.read_text(encoding="utf-8") == peptide_tsv
    assert protein_path.read_text(encoding="utf-8") == protein_tsv
