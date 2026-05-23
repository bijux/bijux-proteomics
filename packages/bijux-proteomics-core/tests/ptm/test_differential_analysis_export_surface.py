# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_differential_volcano_tsv,
    render_ptm_site_differential_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_differential_renderers_preserve_site_and_volcano_ledgers() -> None:
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))
    report = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=features.accepted_records,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )

    result_lines = render_ptm_site_differential_tsv(report.differential_report).splitlines()
    volcano_lines = render_ptm_differential_volcano_tsv(report.volcano_plot).splitlines()

    assert result_lines[0].startswith("site_key\tprotein_ref\tresidue\tposition")
    assert any("P11111:S5:Phospho" in line and "corrected" in line for line in result_lines)
    assert volcano_lines[0] == (
        "site_key\tprotein_ref\tresidue\tposition\tmodification_name\t"
        "raw_log2_fold_change\tcorrected_log2_fold_change\tplotted_log2_fold_change\t"
        "raw_p_value\tadjusted_p_value\tnegative_log10_adjusted_p_value\thighlighted\tprotein_correction_status"
    )
    assert any("P11111:S5:Phospho" in line for line in volcano_lines)
