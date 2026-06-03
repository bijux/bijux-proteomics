# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_ambiguity_review_report,
    build_ptm_localization_scoring_report,
    build_ptm_site_group_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_ambiguity_review_summary_tsv,
    render_ptm_localized_site_review_tsv,
    render_ptm_site_group_quant_matrix_tsv,
    render_ptm_site_group_quant_missingness_tsv,
    render_ptm_site_group_quant_summary_tsv,
    render_ptm_unlocalized_group_review_tsv,
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


def test_ptm_ambiguity_review_renderers_keep_localized_and_unlocalized_ledgers_separate() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    localization = build_ptm_localization_scoring_report(
        evidence.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )
    report = build_ptm_ambiguity_review_report(
        site_table,
        localization_scoring_report=localization,
        protein_sequences=_protein_sequences(),
    )

    summary_lines = render_ptm_ambiguity_review_summary_tsv(report).splitlines()
    localized_lines = render_ptm_localized_site_review_tsv(report).splitlines()
    unlocalized_lines = render_ptm_unlocalized_group_review_tsv(report).splitlines()

    assert summary_lines[0] == (
        "localized_site_count\tunlocalized_group_count\tpossible_residue_count\t"
        "decisive_localized_site_count\tambiguous_group_count"
    )
    assert "P11111:S5:Phospho" in localized_lines[1]
    assert any("P11111:Phospho:17|18|19" in line for line in unlocalized_lines)
    assert any("\tS;T;Y\t" in line for line in unlocalized_lines)


def test_ptm_site_group_quant_renderers_keep_group_matrix_and_missingness_explicit() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    localization = build_ptm_localization_scoring_report(
        evidence.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )
    report = build_ptm_site_group_quantification_report(
        site_table,
        feature_records=features.accepted_records,
        localization_scoring_report=localization,
        protein_sequences=_protein_sequences(),
    )

    summary_lines = render_ptm_site_group_quant_summary_tsv(report).splitlines()
    matrix_lines = render_ptm_site_group_quant_matrix_tsv(report).splitlines()
    missingness_lines = render_ptm_site_group_quant_missingness_tsv(report).splitlines()

    assert (
        summary_lines[0]
        == "group_row_count\tsample_count\tobserved_cell_count\tzero_cell_count\tmissing_cell_count\tfiltered_cell_count"
    )
    assert matrix_lines[0].startswith(
        "group_key\tprotein_ref\tmodification_name\tcandidate_positions\tpossible_residues\tconfidence_tier\t"
    )
    assert any("P11111:Phospho:17|18|19" in line for line in matrix_lines)
    assert missingness_lines[0] == (
        "sample_id\tobserved_count\tzero_count\tnot_observed_count\tfiltered_count"
    )
