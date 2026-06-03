# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmSiteQuantAmbiguityPolicy,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_site_quant_excluded_tsv,
    render_ptm_site_quant_matrix_tsv,
    render_ptm_site_quant_missingness_tsv,
    render_ptm_site_quant_summary_tsv,
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


def test_ptm_site_quantification_tsv_renderers_preserve_matrix_and_exclusions() -> None:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
        ambiguity_policy=PtmSiteQuantAmbiguityPolicy.EXCLUDE,
    )

    summary_tsv = render_ptm_site_quant_summary_tsv(report)
    matrix_tsv = render_ptm_site_quant_matrix_tsv(report)
    missingness_tsv = render_ptm_site_quant_missingness_tsv(report)
    excluded_tsv = render_ptm_site_quant_excluded_tsv(report)

    assert summary_tsv.splitlines()[0].startswith("ambiguity_policy\tsite_row_count")
    assert "localization_tier" in matrix_tsv.splitlines()[0]
    assert "P11111:S5:Phospho" in matrix_tsv
    assert "P11111:S17:Phospho" not in matrix_tsv
    assert "C1\t1\t0\t2\t0" in missingness_tsv
    assert excluded_tsv.splitlines()[0].startswith("site_key\tgroup_key\tprotein_ref")
    assert "P11111:S17:Phospho\tP11111:Phospho:17|18|19" in excluded_tsv
