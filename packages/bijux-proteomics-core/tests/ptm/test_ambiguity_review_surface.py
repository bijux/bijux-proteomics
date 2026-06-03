# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_ambiguity_review_report,
    build_ptm_localization_scoring_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
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


def test_ptm_ambiguity_review_report_separates_localized_sites_from_unlocalized_groups() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
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

    assert report.summary.localized_site_count == 3
    assert report.summary.unlocalized_group_count == 2
    localized = next(
        entry
        for entry in report.localized_sites
        if entry.site_key == "P11111:S5:Phospho"
    )
    assert localized.confidence_tier.value == "supported"
    ambiguous = next(
        entry
        for entry in report.unlocalized_groups
        if entry.group_key == "P11111:Phospho:17|18|19"
    )
    assert ambiguous.possible_residues == ("S", "T", "Y")
    assert ambiguous.localization_probability == 0.715
    assert ambiguous.confidence_tier.value == "supported"
