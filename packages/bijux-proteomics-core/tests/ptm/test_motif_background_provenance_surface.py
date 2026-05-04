# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
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
    fasta = Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / "ptm_sites.fasta"
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

    report = build_ptm_motif_enrichment_background_provenance_report(
        site_entries,
        protein_sequences=_protein_sequences(),
        modification_name="Phospho",
        background_universe="all_serine_threonine_tyrosine_residues_in_observed_proteins",
        applied_filters=(
            "exclude_decoy_sites",
            "require_localization_score_ge_0.75",
        ),
    )

    assert report.modification_name == "Phospho"
    assert report.background_universe.startswith("all_serine")
    assert report.statistical_test == "fisher_exact"
    assert report.multiple_testing_correction == "benjamini_hochberg"
    assert report.foreground_site_count >= 1
    assert report.background_site_count >= report.foreground_site_count
    assert any(term.residue == "S" for term in report.terms)
