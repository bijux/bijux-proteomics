# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_occupancy_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
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


def test_ptm_site_occupancy_report_links_modified_and_unmodified_forms() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_entries = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    )

    target = next(
        entry
        for entry in report.entries
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "C1"
    )

    assert target.modified_intensity == 120.0
    assert target.unmodified_intensity == 880.0
    assert target.confidence_tier.value == "high_confidence"
    assert target.modified_peptides == ("S[Phospho]PEPTIDEK",)
    assert target.unmodified_peptides == ("SPEPTIDEK",)
    assert target.modified_feature_count == 1
    assert target.unmodified_feature_count == 1


def test_ptm_site_occupancy_report_marks_missing_counterparts_and_ambiguity() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_entries = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    feature_records = tuple(
        record
        for record in feature_records
        if not (record.sample_id == "T2" and record.canonical_peptide == "SPEPTIDEK")
    )

    report = build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    )

    assert report.summary.missing_counterpart_count >= 1
    assert report.summary.ambiguous_site_count >= 1
    missing_entry = next(
        entry
        for entry in report.entries
        if entry.confidence_tier.value == "missing_unmodified_evidence"
    )
    ambiguous_entry = next(
        entry
        for entry in report.entries
        if entry.confidence_tier.value == "ambiguous_site"
    )

    assert report.summary.high_confidence_count >= 1
    assert report.summary.missing_unmodified_evidence_count >= 1
    assert (
        missing_entry.unmodified_feature_count == 0
        or missing_entry.modified_feature_count == 0
    )
    assert missing_entry.uncertainty.value == "missing_counterpart"
    assert ambiguous_entry.modified_peptides


def test_ptm_site_occupancy_report_tracks_missing_modified_evidence_explicitly() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_entries = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    feature_records = tuple(
        record
        for record in feature_records
        if not (
            record.sample_id == "C1"
            and record.canonical_peptide == "S[Phospho]PEPTIDEK"
        )
    )

    report = build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    )

    missing_modified = next(
        entry
        for entry in report.entries
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "C1"
    )

    assert missing_modified.confidence_tier.value == "missing_modified_evidence"
    assert missing_modified.uncertainty.value == "missing_counterpart"
    assert missing_modified.modified_feature_count == 0
