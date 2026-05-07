# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    PtmLabTargetingDisposition,
    PtmLocalizationConfidenceTier,
    PtmMotifCredibilityDisposition,
    build_ptm_ambiguity_propagation_benchmark_report,
    build_ptm_lab_targeting_rubric_report,
    build_ptm_localization_confidence_benchmark_report,
    build_ptm_motif_credibility_benchmark_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
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


def test_ptm_ambiguity_propagation_benchmark_report_downgrades_ambiguous_sites() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_ambiguity_propagation_benchmark_report(
        sites,
        feature_records=features,
    )

    propagated = next(entry for entry in report.entries if entry.propagated_to_quant)
    interpretive_only = next(entry for entry in report.entries if entry.interpretive_only)

    assert propagated.localization_ambiguous is True
    assert propagated.ambiguous_occupancy_count >= 1
    assert interpretive_only.missing_counterpart_count >= 0
    assert report.interpretive_only_count >= 1


def test_ptm_motif_credibility_benchmark_report_blocks_small_ambiguous_motif_claims() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)

    report = build_ptm_motif_credibility_benchmark_report(
        sites,
        protein_sequences=_protein_sequences(),
        modification_name="Phospho",
    )

    assert report.disposition is PtmMotifCredibilityDisposition.INTERPRETIVE_ONLY
    assert report.foreground_site_count >= 1
    assert report.caveats


def test_ptm_lab_targeting_rubric_report_separates_targetable_and_interpretive_sites() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_lab_targeting_rubric_report(
        parsed.accepted_records,
        mappings,
        sites,
        feature_records=features,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )

    targetable = next(
        entry
        for entry in report.entries
        if entry.disposition is PtmLabTargetingDisposition.TARGETABLE
    )
    interpretive = next(
        entry
        for entry in report.entries
        if entry.disposition is PtmLabTargetingDisposition.INTERPRETIVE_ONLY
    )

    assert targetable.localization_confidence_tier is PtmLocalizationConfidenceTier.DECISIVE
    assert targetable.occupancy_complete is True
    assert interpretive.rationale
    assert report.interpretive_only_count >= 1
