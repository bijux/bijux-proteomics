# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmProteinCorrectionMode,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
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


def test_ptm_report_export_writes_required_tables_and_manifest(tmp_path: Path) -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    design_entries = parse_experimental_design_table(
        _ptm_fixture("ptm.design.tsv")
    ).accepted_entries
    report = build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=features.accepted_records,
        design_entries=design_entries,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )

    manifest = export_ptm_report_bundle(report, tmp_path / "ptm_report")
    output_dir = tmp_path / "ptm_report"

    assert manifest.summary.accepted_evidence_count == 8
    assert manifest.summary.quantified_site_row_count == 5
    assert manifest.summary.differential_site_count == 5
    assert manifest.motif_summary_included is True
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.peptide_tsv).exists()
    assert (output_dir / manifest.artifacts.site_tsv).exists()
    assert (output_dir / manifest.artifacts.localization_tsv).exists()
    assert (output_dir / manifest.artifacts.site_quant_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.motif_term_tsv).exists()
    assert "S[Phospho]PEPTIDEK" in (
        output_dir / manifest.artifacts.peptide_tsv
    ).read_text()
    assert "P11111:S5:Phospho" in (
        output_dir / manifest.artifacts.site_tsv
    ).read_text()
    assert "probability_source" in (
        output_dir / manifest.artifacts.localization_tsv
    ).read_text()
    assert "P11111:S5:Phospho" in (
        output_dir / manifest.artifacts.site_quant_matrix_tsv
    ).read_text()
    assert "corrected_log2_fold_change" in (
        output_dir / manifest.artifacts.differential_tsv
    ).read_text()
    assert "exclusive_to_regulated" in (
        output_dir / manifest.artifacts.motif_term_tsv
    ).read_text()
