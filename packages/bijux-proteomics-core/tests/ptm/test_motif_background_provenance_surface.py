# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmMotifBackgroundMode,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_ptm_motif_enrichment_background_provenance_report,
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


def test_ptm_motif_enrichment_background_report_preserves_provenance() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )
    site_entries = build_ptm_site_table(mappings)

    observed_report = build_ptm_motif_enrichment_background_provenance_report(
        site_entries,
        protein_sequences=_protein_sequences(),
        modification_name="Phospho",
        background_mode=PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND,
        applied_filters=(
            "exclude_decoy_sites",
            "require_localization_score_ge_0.75",
        ),
    )
    whole_proteome_report = build_ptm_motif_enrichment_background_provenance_report(
        site_entries,
        protein_sequences=_protein_sequences(),
        modification_name="Phospho",
        background_mode=PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND,
        applied_filters=(
            "exclude_decoy_sites",
            "require_localization_score_ge_0.75",
        ),
    )

    assert observed_report.modification_name == "Phospho"
    assert (
        observed_report.background_mode
        is PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND
    )
    assert (
        whole_proteome_report.background_mode
        is PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND
    )
    assert observed_report.background_universe == "observed_phosphosite_background"
    assert whole_proteome_report.background_universe == "whole_proteome_background"
    assert observed_report.statistical_test == "fisher_exact"
    assert observed_report.multiple_testing_correction == "benjamini_hochberg"
    assert observed_report.foreground_site_count >= 1
    assert (
        whole_proteome_report.background_site_count
        > observed_report.background_site_count
    )
    assert any(term.residue == "S" for term in observed_report.terms)
