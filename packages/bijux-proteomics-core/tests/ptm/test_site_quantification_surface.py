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


def test_ptm_site_quantification_report_builds_site_by_sample_matrix() -> None:
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
    )

    assert report.summary.site_row_count == 3
    assert report.summary.sample_count == 4
    assert report.summary.ambiguous_row_count == 2
    assert report.summary.ambiguous_group_row_count == 2
    target = next(row for row in report.rows if row.site_key == "P11111:S5:Phospho")
    low_localization = next(
        row for row in report.rows if row.site_key == "Q9DEC1:S5:Phospho"
    )
    lookup = {value.sample_id: value for value in target.values}

    assert lookup["C1"].abundance == 120.0
    assert lookup["C2"].abundance == 180.0
    assert lookup["T1"].abundance == 710.0
    assert lookup["T2"].abundance == 790.0
    assert target.localization_tier.value == "supported"
    assert low_localization.localization_tier.value == "refused"


def test_ptm_site_quantification_report_routes_ambiguous_signal_to_group_matrix() -> (
    None
):
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
    )

    assert all(row.ambiguous is False for row in report.rows)
    assert all(row.site_key != "P11111:S17:Phospho" for row in report.rows)
    assert report.ambiguous_group_quantification is not None
    ambiguous = next(
        row
        for row in report.ambiguous_group_quantification.rows
        if row.group_key == "P11111:Phospho:17|18|19"
    )
    lookup = {value.sample_id: value for value in ambiguous.values}

    assert lookup["C1"].abundance == 60.0
    assert lookup["T1"].abundance == 140.0


def test_ptm_site_quantification_report_can_exclude_ambiguous_sites() -> None:
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

    assert report.ambiguity_policy is PtmSiteQuantAmbiguityPolicy.EXCLUDE
    assert report.summary.site_row_count == 3
    assert report.summary.ambiguous_group_row_count == 0
    assert report.summary.excluded_ambiguous_row_count == 2
    assert report.ambiguous_group_quantification is None
    assert report.excluded_ambiguous_site_keys == (
        "P11111:S17:Phospho",
        "P22222:S4:Phospho",
    )
    excluded = next(
        row
        for row in report.excluded_ambiguous_rows
        if row.site_key == "P11111:S17:Phospho"
    )
    assert excluded.group_key == "P11111:Phospho:17|18|19"
    assert excluded.localized_peptides == ("AS[Phospho]TYK",)
