# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    PtmLocalizationConfidenceTier,
    build_ptm_localization_confidence_benchmark_report,
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


def test_ptm_localization_confidence_benchmark_report_scores_decisive_and_ambiguous_sites() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    report = build_ptm_localization_confidence_benchmark_report(
        parsed.accepted_records,
        mappings,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )

    decisive = next(
        entry
        for entry in report.entries
        if entry.confidence_tier is PtmLocalizationConfidenceTier.DECISIVE
    )
    ambiguous = next(
        entry
        for entry in report.entries
        if entry.confidence_tier is PtmLocalizationConfidenceTier.AMBIGUOUS
    )

    assert decisive.localization_probability >= 0.95
    assert decisive.fragment_ion_count >= 2
    assert ambiguous.ambiguity_present is True
    assert report.ambiguous_count >= 1
