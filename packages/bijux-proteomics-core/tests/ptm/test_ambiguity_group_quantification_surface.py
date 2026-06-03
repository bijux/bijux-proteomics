# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_localization_scoring_report,
    build_ptm_site_group_quantification_report,
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


def test_ptm_site_group_quantification_report_preserves_unresolved_group_signal() -> (
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

    assert report.summary.group_row_count == 2
    target = next(
        row for row in report.rows if row.group_key == "P11111:Phospho:17|18|19"
    )
    values = {value.sample_id: value for value in target.values}

    assert target.possible_residues == ("S", "T", "Y")
    assert target.localization_probability == 0.715
    assert target.confidence_tier.value == "supported"
    assert values["C1"].abundance == 60.0
    assert values["T1"].abundance == 140.0
    assert values["C1"].contributing_feature_count == 1
    assert values["T1"].contributing_feature_count == 1
